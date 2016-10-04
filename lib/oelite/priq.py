import heapq

class PriorityQueue:
    def __init__(self, initial=None, key=lambda x:x):
       self.key = key
       self.serial = 0
       if initial:
           self._data = [(key(item), self.nextserial(), item) for item in initial]
           heapq.heapify(self._data)
       else:
           self._data = []

    def nextserial(self):
        ret = self.serial
        self.serial += 1
        return ret

    def push(self, item):
        heapq.heappush(self._data, (self.key(item), self.nextserial(), item))

    def pop(self):
        return heapq.heappop(self._data)[2]

    def __len__(self):
        return len(self._data)
