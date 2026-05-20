from collections import OrderedDict
from .base import Policy

class ARC(Policy):
    def __init__(self, capacity: int):
        super().__init__(capacity)
        self.c = capacity
        self.p = 0                            
        self.T1: OrderedDict = OrderedDict()  
        self.T2: OrderedDict = OrderedDict()  
        self.B1: OrderedDict = OrderedDict()  
        self.B2: OrderedDict = OrderedDict()  

    def access(self, page: int) -> bool:  
        if page in self.T1:
            del self.T1[page]
            self.T2[page] = None   
            self.hits += 1
            return True
        if page in self.T2:
            self.T2.move_to_end(page, last=True)
            self.hits += 1
            return True

      
        self.faults += 1

        if page in self.B1:
            delta = max(1, len(self.B2) // max(1, len(self.B1)))
            self.p = min(self.c, self.p + delta)
            self._replace(page)
            del self.B1[page]
            self.T2[page] = None
            self.resident = set(self.T1) | set(self.T2)
            return False

        if page in self.B2:
            delta = max(1, len(self.B1) // max(1, len(self.B2)))
            self.p = max(0, self.p - delta)
            self._replace(page)
            del self.B2[page]
            self.T2[page] = None
            self.resident = set(self.T1) | set(self.T2)
            return False

        L1_size = len(self.T1) + len(self.B1)
        L2_size = len(self.T2) + len(self.B2)
        if L1_size == self.c:
            if len(self.T1) < self.c:
                # Drop LRU of B1, then replace.
                self.B1.popitem(last=False)
                self._replace(page)
            else:
  
                evicted, _ = self.T1.popitem(last=False)
    
                _ = evicted
        elif L1_size < self.c and (L1_size + L2_size) >= self.c:
            if (L1_size + L2_size) == 2 * self.c:
                self.B2.popitem(last=False)
            self._replace(page)

        self.T1[page] = None
        self.resident = set(self.T1) | set(self.T2)
        return False


    def _replace(self, incoming: int) -> None:
        """REPLACE subroutine from the paper.

        Evict one page from T1 or T2 (and ghost it into B1 or B2) so that
        we maintain |T1| + |T2| <= c.
        """
        if self.T1 and (
            len(self.T1) > self.p
            or (incoming in self.B2 and len(self.T1) == self.p)
        ):

            evicted, _ = self.T1.popitem(last=False)
            self.B1[evicted] = None
        else:
  
            evicted, _ = self.T2.popitem(last=False)
            self.B2[evicted] = None

    def _on_hit(self, page: int) -> None:
        pass

    def _on_miss_with_room(self, page: int) -> None:
        pass

    def _evict(self, incoming: int) -> int:
        raise NotImplementedError

    def state(self) -> dict:
        return {
            "p": self.p,
            "T1": list(self.T1),
            "T2": list(self.T2),
            "B1": list(self.B1),
            "B2": list(self.B2),
        }
