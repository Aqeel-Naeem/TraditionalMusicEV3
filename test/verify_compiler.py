import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from songs import compile_song_timelines, list_songs, get_song

for name in list_songs():
    notes = get_song(name)
    timelines = compile_song_timelines(notes)
    print(f'Song "{name}": generated {len(timelines)} brick timeline(s)')
    for mac, data in timelines.items():
        print(f'   Brick {mac}: {len(data)} bytes')

print("All song timelines compiled successfully with zero errors!")
