class Queue:

    def __init__(self):
        self.events_list = []
        self.events_list_added_order = []

    def add(self, event, first=False):
        if first:
            self.append_as_first(event)
        else:
            self.append_chronologically(event)
        self.append_added_order(event)

    def add_bulk(self, events):
        for event in events:
            self.add(event)

    def get(self):
        return self.events_list[0] if self.events_list else None

    def pop(self):
        if self.events_list:
            last = self.events_list[0]
            del(self.events_list[0])
            return last
        else:
            return None

    def append_as_first(self, event):
        self.events_list.insert(0, event)

    def append_chronologically(self, event):
        if not self.events_list:  # queue empty, add first item
            self.events_list.append(event)
        else:
            for order, existing_event in enumerate(self.events_list):
                if event.execution_date > self.events_list[-1].execution_date:
                    self.events_list.append(event)
                    break
                if event.execution_date < existing_event.execution_date:
                    self.events_list.insert(order, event)
                    break

    def append_added_order(self, event):
        self.events_list_added_order.append(event)

    def __len__(self):
        return len(self.events_list)

    def get_length(self):
        return len(self.events_list)

    def is_event_in_queue(self, event):
        return event in self.events_list

    def get_index_order_of_event(self, event):
        try:
            return self.events_list.index(event)
        except ValueError:
            return -1

    def remove_event_by_id(self, id):
        for event in self.events_list:
            if event.event_id == id:
                try:
                    return self.events_list.remove(event)
                except (ValueError, TypeError):
                    raise