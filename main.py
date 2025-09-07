import time
import numpy as np
import sounddevice as sd
from collections import deque

# ---- Tunables (adjust if needed) ----
SAMPLE_RATE      = 44100       # 48k/44.1k both fine
BLOCK_SIZE       = 1024        # ~23 ms at 44.1k
CALIBRATION_SEC  = 2.0         # learn room noise for this long
ATTACK_FACTOR    = 6.0         # energy must exceed (noise_mean + ATTACK_FACTOR*noise_std) to turn ON
RELEASE_FACTOR   = 2.5         # drop below (noise_mean + RELEASE_FACTOR*noise_std) to turn OFF
MIN_ON_TIME_SEC  = 0.08        # minimum time to stay ON (debounce)
MIN_OFF_TIME_SEC = 0.05        # minimum time to stay OFF
PREEMPHASIS      = 0.97        # mild HF boost to emphasize percussive transients; set 0 to disable
INPUT_DEVICE     = None        # set to an int (index) or str (name) from sd.query_devices(); None = default

# -------------------------------------

state = "OFF"
last_change = 0.0

# Rolling stats for noise floor
energy_hist = deque(maxlen=int((CALIBRATION_SEC * SAMPLE_RATE) // BLOCK_SIZE))

def frame_energy(x):
    # optional preemphasis to highlight attacks
    if PREEMPHASIS and PREEMPHASIS > 0:
        x = np.append(x[0], x[1:] - PREEMPHASIS * x[:-1])
    # RMS energy in dB-like units (log)
    # add tiny epsilon to avoid log(0)
    rms = np.sqrt(np.mean(x.astype(np.float32)**2) + 1e-12)
    # convert to linear "energy" measure that behaves nicely for thresholds
    return 20.0 * np.log10(rms + 1e-12)

def current_thresholds():
    if len(energy_hist) < max(4, energy_hist.maxlen or 4):
        # not calibrated yet: set very high thresholds so we don't trigger early
        return float("inf"), float("inf")
    mu = np.mean(energy_hist)
    sdv = np.std(energy_hist) + 1e-6
    attack_th = mu + ATTACK_FACTOR * sdv
    release_th = mu + RELEASE_FACTOR * sdv
    return attack_th, release_th

def on_audio(indata, frames, time_info, status):
    global state, last_change

    if status:
        # You can print(status) for debugging device issues
        pass

    # If stereo, mix to mono
    x = indata
    if x.ndim == 2:
        x = np.mean(x, axis=1)
    e = frame_energy(x)

    # Update rolling noise stats, but limit how much ON frames contaminate it
    # Only push into history if we're OFF (i.e., likely noise/room level)
    if state == "OFF":
        energy_hist.append(e)

    attack_th, release_th = current_thresholds()
    now = time.monotonic()

    if state == "OFF":
        if e > attack_th and (now - last_change) >= MIN_OFF_TIME_SEC:
            state = "ON"
            last_change = now
            print("ON")
    else:  # state == "ON"
        if e < release_th and (now - last_change) >= MIN_ON_TIME_SEC:
            state = "OFF"
            last_change = now
            print("OFF")

def main():
    print("Calibrating noise floor for ~{}s...".format(CALIBRATION_SEC))
    with sd.InputStream(
        device=INPUT_DEVICE,
        channels=1,
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="float32",
        callback=on_audio,
    ):
        # Run until Ctrl+C
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting.")

if __name__ == "__main__":
    main()
