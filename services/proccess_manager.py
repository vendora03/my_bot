class Process_Handler:
    def __init__(self):
        self.sedang_diproses = set()
    
    def is_processing(self, user_id):
        return user_id in self.sedang_diproses
    
    def start_processing(self, user_id):
        self.sedang_diproses.add(user_id)
    
    def finish_processing(self, user_id):
        if user_id in self.sedang_diproses:
            self.sedang_diproses.remove(user_id)

ProccessManager = Process_Handler()