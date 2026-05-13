from . import backend_model

# Only import queue_job if the queue_job module is installed
try:
    from odoo.addons import queue_job as _queue_job_module
    from . import queue_job
except ImportError:
    pass
