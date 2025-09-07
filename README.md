# RPi5-Mallet-SoundBrite
This project uses a Raspberry Pi 5 and a USB Microphone to recognize notes played by mallets (percussion instrument)


# Instructions
You can list audio input devices with:
python3 -c "import sounddevice as sd; print(sd.query_devices())"
Please note the input device index (or name) you wish to use.

# How it Works and What to Tweak
The first ~2 seconds, it learns your room noise (CALIBRATION_SEC). Be quiet during that period.
It computes frame energy in short blocks and compares to adaptive thresholds.
If you get false triggers:
Increase ATTACK_FACTOR (e.g., 7.5 → fewer ONs).
Increase MIN_ON_TIME_SEC (e.g., 0.12) to avoid flicker.
If it misses hits:
Decrease ATTACK_FACTOR (e.g., 4.5).
Reduce RELEASE_FACTOR (e.g., 2.0) so it turns OFF sooner and is ready for the next hit.
Consider lowering BLOCK_SIZE to ~512 for faster reaction.
