import time


class Cache:
    class Node:
        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.prev = None
            self.next = None
            self.last_accessed_time = time.time()

    def __init__(self, capacity, ttl_millis):
        self.capacity = capacity
        self.ttl_millis = ttl_millis
        self.cache = {}
        self.head = self.Node(None, None)
        self.tail = self.Node(None, None)
        self.head.next = self.tail
        self.tail.prev = self.head

    def _add_node(self, node):
        node.prev = self.head
        node.next = self.head.next
        self.head.next.prev = node
        self.head.next = node

    def _remove_node(self, node):
        prev = node.prev
        next_node = node.next
        prev.next = next_node
        next_node.prev = prev

    def _move_to_head(self, node):
        self._remove_node(node)
        self._add_node(node)

    def get(self, key):
        if key in self.cache:
            node = self.cache[key]
            current_time = time.time()
            if (current_time - node.last_accessed_time) * 1000 <= self.ttl_millis:
                node.last_accessed_time = current_time  # Update last accessed time
                self._move_to_head(node)
                return node.value
            else:
                # Node has expired, remove it from the cache
                self._remove_node(node)
                del self.cache[key]
        return None

    def put(self, key, value):
        if key in self.cache:
            node = self.cache[key]
            node.value = value
            node.last_accessed_time = time.time()  # Update last accessed time
            self._move_to_head(node)
        else:
            if len(self.cache) >= self.capacity:
                # Evict the least recently used node (tail's prev)
                tail_prev = self.tail.prev
                self._remove_node(tail_prev)
                del self.cache[tail_prev.key]

            new_node = self.Node(key, value)
            self._add_node(new_node)
            self.cache[key] = new_node
