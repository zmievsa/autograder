# with Timer(print) as timer:
#   ...
#   optional:
#   with timer.make_subtimer(turn_off_gc=True, handler=lambda m: print(f"Subtimer 1 result: {m}")) as subtimer1:
#       ...
#   with timer.make_subtimer(handler=yourfunction) as subtimer2:
#       ...
# >>> Subtimer 1: subtimer1_result
# >>> Subtimer 2: subtimer2_result
# >>> Your_main_timer_result sum_of_your_subtimer_results


from time import time
import gc


class Timer:
    """ A thread/process unsafe timer for easy timing of code execution """
    def __init__(self, handler=None, turn_off_gc=False):
        self.start = 0
        self.end = 0
        self.handler = handler
        self.turn_off_gc = turn_off_gc
        self.subtimers = []

    def __enter__(self):
        self.start = time()
        if (self.turn_off_gc):
            self.gc_was_enabled = gc.isenabled()
            gc.disable()
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
        if self.turn_off_gc and self.gc_was_enabled:
            gc.enable()
    
    def _calculate_expected_result(self):
        return sum([t.result for t in self.subtimers])
    
    def make_subtimer(self, *args, **kwargs):
        timer = type(self)(*args, **kwargs)
        self.subtimers.append(timer)
        return timer

