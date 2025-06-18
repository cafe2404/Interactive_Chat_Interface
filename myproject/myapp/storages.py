import os
from django.core.files.storage import FileSystemStorage

class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        # Xoá file cũ nếu tồn tại
        if self.exists(name):
            os.remove(os.path.join(self.location, name))
        return name


