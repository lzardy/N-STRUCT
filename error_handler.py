def handle_errors(func):
   def wrapper(*args, **kwargs):
       try:
           return func(*args, **kwargs)
       except Exception as e:
           print(f"An error occurred in {func.__name__}: {e}")
   return wrapper