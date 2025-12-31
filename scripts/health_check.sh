#!/bin/bash
# NSE Scraper - Health Monitoring Script
# Add to crontab for continuous monitoring

set -e

# Configuration
API_URL="http://localhost:1020/health"
LOG_FILE="/var/log/nse-scraper-health.log"
ALERT_EMAIL=""  # Set your email for alerts (optional)
SLACK_WEBHOOK=""  # Set Slack webhook URL for alerts (optional)

# Colors (for terminal output)
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Function to log messages
log_message() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
    echo -e "$1"
}

# Function to send alert
send_alert() {
    local message="$1"
    
    # Log the alert
    log_message "[ALERT] $message"
    
    # Send email alert (if configured)
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "NSE Scraper Alert" "$ALERT_EMAIL" 2>/dev/null || true
    fi
    
    # Send Slack alert (if configured)
    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 NSE Scraper Alert: $message\"}" \
            "$SLACK_WEBHOOK" 2>/dev/null || true
    fi
}

# Function to check health
check_health() {
    local response
    local http_code
    
    # Make health check request
    response=$(curl -s -w "\n%{http_code}" "$API_URL" 2>/dev/null)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" -eq 200 ]; then
        log_message "${GREEN}[OK]${NC} Health check passed (HTTP $http_code)"
        
        # Parse response for additional info
        if command -v jq &> /dev/null; then
            status=$(echo "$body" | jq -r '.status // "unknown"')
            log_message "  Status: $status"
        fi
        
        return 0
    else
        log_message "${RED}[FAIL]${NC} Health check failed (HTTP $http_code)"
        return 1
    fi
}

# Function to check container status
check_container() {
    local status
    status=$(docker inspect --format='{{.State.Status}}' nse-scraper 2>/dev/null || echo "not_found")
    
    if [ "$status" == "running" ]; then
        log_message "${GREEN}[OK]${NC} Container is running"
        return 0
    else
        log_message "${RED}[FAIL]${NC} Container status: $status"
        return 1
    fi
}

# Function to check resource usage
check_resources() {
    local stats
    stats=$(docker stats nse-scraper --no-stream --format "CPU: {{.CPUPerc}}, Memory: {{.MemUsage}}" 2>/dev/null || echo "N/A")
    log_message "  Resources: $stats"
}

# Function to restart container if unhealthy
auto_restart() {
    log_message "Attempting auto-restart..."
    
    cd ~/NSE-Scraper
    docker-compose -f docker-compose.prod.yml restart
    
    # Wait for startup
    sleep 30
    
    # Check again
    if check_health; then
        log_message "${GREEN}[OK]${NC} Auto-restart successful"
        send_alert "NSE Scraper was automatically restarted and is now healthy"
    else
        log_message "${RED}[FAIL]${NC} Auto-restart failed"
        send_alert "NSE Scraper auto-restart failed! Manual intervention required."
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "NSE Scraper Health Check - $TIMESTAMP"
    echo "=========================================="
    
    # Check container
    if ! check_container; then
        send_alert "Container is not running"
        auto_restart
        exit 1
    fi
    
    # Check health endpoint
    if ! check_health; then
        send_alert "Health check failed"
        auto_restart
        exit 1
    fi
    
    # Check resources
    check_resources
    
    echo "=========================================="
}

# Run main function
main

# Rotate log file if too large (> 10MB)
if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt 10485760 ]; then
    mv "$LOG_FILE" "${LOG_FILE}.old"
fi
