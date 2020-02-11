from time import time

class Timer:
    def __init__(self, handler=None):
        self.start = 0
        self.end = 0
        self.handler = handler
        self.subtimers = []

    def __enter__(self):
        self.start = time()
        return self

    def __exit__(self, type, value, traceback):
        self.end = time()
        self.result = self.end - self.start
        self.expected_result = self._calculate_expected_result()
        if self.handler is not None:
            if self.subtimers:
                self.handler(self.expected_result, self.result)
            else:
                self.handler(self.result)
    
    def _calculate_expected_result(self):
        return sum([t.result for t in self.subtimers])
    
    def make_subtimer(self, *args, **kwargs):
        timer = type(self)(*args, **kwargs)
        self.subtimers.append(timer)
        return timer

