from GtkHelper.ComboRow import SimpleComboRowItem

import threading
import time
import psutil

# The methods that can be selected in the "Usage Method" row of the cpu actions
USAGE_METHODS = ["average", "max-core"]

SAMPLE_INTERVAL = 1
FIRST_SAMPLE_INTERVAL = 0.15

def get_usage_method_items() -> list[SimpleComboRowItem]:
    return [SimpleComboRowItem("average", "Average of all cores"),
            SimpleComboRowItem("max-core", "Highest single core")]

class CPUSampler(threading.Thread):
    """
    Samples the cpu usage on its own thread and hands the last reading to every cpu action.

    psutil measures the usage since the last call made by the *calling thread*, so letting each
    action call it directly makes the readings depend on what the other actions did in between.
    Two actions on the same key are ticked one after the other in the same thread, which left the
    second one measuring nothing but the work of the first (the graph rendering, for example).
    """

    def __init__(self):
        super().__init__(daemon=True, name="OSPluginCPUSampler")

        self.lock = threading.Lock()
        self.average = 0.0
        self.max_core = 0.0

    def run(self):
        # The first reading of each is meaningless, psutil needs a previous one to compare against
        psutil.cpu_percent()
        psutil.cpu_percent(percpu=True)

        # The first window is kept short so the actions don't show 0% for a whole tick on startup
        interval = FIRST_SAMPLE_INTERVAL

        while True:
            time.sleep(interval)
            interval = SAMPLE_INTERVAL

            average = psutil.cpu_percent()
            per_core = psutil.cpu_percent(percpu=True)

            with self.lock:
                self.average = average
                self.max_core = max(per_core) if per_core else 0.0

    def get_percent(self, method: str) -> float:
        with self.lock:
            return self.max_core if method == "max-core" else self.average

_sampler: CPUSampler | None = None
_sampler_lock = threading.Lock()

def get_sampler() -> CPUSampler:
    global _sampler
    with _sampler_lock:
        if _sampler is None:
            _sampler = CPUSampler()
            _sampler.start()
    return _sampler

def get_cpu_percent(method: str) -> float:
    return get_sampler().get_percent(method)
