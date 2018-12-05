def ts_to_hms(t):
  seconds = int(t)
  minutes = (seconds // 60)
  seconds -= minutes * 60
  hours = (minutes // 60)
  minutes -= hours * 60
  hours = hours % 24
  return hours, minutes, seconds
