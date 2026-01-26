import threading
import uvicorn
import logging
from Loader.server import apiserver
from Utils.config_reader import configure
from Services.cron_jobs import CronJobManager

# Reduce uvicorn logging verbosity
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

if __name__ == '__main__':
    # Start cron job scheduler in a background thread
    cron_manager = CronJobManager()
    threading.Thread(target=cron_manager.run_cron_jobs, daemon=True).start()

    # Start API server
    uvicorn.run(
        apiserver, 
        host=configure.get("SERVER", "HOST"), 
        port=configure.getint("SERVER", "PORT")
    )

