from pathlib import Path

import pygame


AMBIENT_VOLUME = 0.24
DRIVE_VOLUME = 0.28
PICKUP_HORN_VOLUME = 0.28
TRAFFIC_HORN_VOLUME = 0.24
UI_CLICK_VOLUME = 0.22
FINISH_JINGLE_VOLUME = 0.3
DUCKED_AMBIENT_VOLUME = 0.16


class AudioManager:
    def __init__(self):
        self.assets_dir = Path(__file__).resolve().parents[1] / "audio"
        self.enabled = False
        self.ambient_enabled = True
        self.ambient_started = False
        self.drive_loop_active = False
        self.drive_channel = None
        self.effect_channels = []
        self.effect_index = 0
        self.sounds = {}

        self._init_mixer()
        self._load_assets()

    def _init_mixer(self):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(8)
            self.drive_channel = pygame.mixer.Channel(1)
            self.effect_channels = [pygame.mixer.Channel(2), pygame.mixer.Channel(3)]
            self.enabled = True
        except pygame.error as exc:
            print(f"Audio deshabilitado: {exc}")
            self.enabled = False

    def _load_assets(self):
        if not self.enabled:
            return

        self._load_sound("road_loop", "road_loop.wav", DRIVE_VOLUME)
        self._load_sound("pickup_horn", "pickup_horn.wav", PICKUP_HORN_VOLUME)
        self._load_sound("traffic_horn", "traffic_horn.wav", TRAFFIC_HORN_VOLUME)
        self._load_sound("ui_click", "ui_click.wav", UI_CLICK_VOLUME)
        self._load_sound("finish_jingle", "finish_jingle.wav", FINISH_JINGLE_VOLUME)

    def _load_sound(self, key, filename, volume):
        path = self.assets_dir / filename
        if not path.exists():
            print(f"Audio faltante: {path}")
            return

        try:
            sound = pygame.mixer.Sound(path.as_posix())
            sound.set_volume(volume)
            self.sounds[key] = sound
        except pygame.error as exc:
            print(f"No se pudo cargar {filename}: {exc}")

    def play_ambient(self):
        if not self.enabled or not self.ambient_enabled:
            return

        if self.ambient_started and pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(self._ambient_volume_target())
            return

        path = self.assets_dir / "lofi_ambient.wav"
        if not path.exists():
            print(f"Audio faltante: {path}")
            return

        try:
            pygame.mixer.music.load(path.as_posix())
            pygame.mixer.music.set_volume(self._ambient_volume_target())
            pygame.mixer.music.play(-1, fade_ms=900)
            self.ambient_started = True
        except pygame.error as exc:
            print(f"No se pudo iniciar la música ambiente: {exc}")

    def start_drive_loop(self):
        if not self.enabled or self.drive_channel is None:
            return

        sound = self.sounds.get("road_loop")
        if sound is None:
            return

        self.drive_loop_active = True
        if not self.drive_channel.get_busy():
            self.drive_channel.play(sound, loops=-1, fade_ms=250)
        if self.ambient_started and self.ambient_enabled:
            pygame.mixer.music.set_volume(self._ambient_volume_target())

    def stop_drive_loop(self):
        if not self.enabled:
            return

        self.drive_loop_active = False
        if self.drive_channel is not None:
            self.drive_channel.fadeout(250)
        if self.ambient_started and self.ambient_enabled:
            pygame.mixer.music.set_volume(self._ambient_volume_target())

    def play_pickup_horn(self):
        self._play_effect("pickup_horn")

    def play_traffic_horn(self):
        self._play_effect("traffic_horn")

    def play_ui_click(self):
        self._play_effect("ui_click")

    def play_finish_jingle(self):
        self._play_effect("finish_jingle")

    def set_ambient_enabled(self, enabled):
        self.ambient_enabled = enabled
        if not self.enabled:
            return

        if not enabled:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(250)
            self.ambient_started = False
            return

        self.play_ambient()

    def _play_effect(self, key):
        if not self.enabled or not self.effect_channels:
            return

        sound = self.sounds.get(key)
        if sound is None:
            return

        channel = self.effect_channels[self.effect_index % len(self.effect_channels)]
        self.effect_index += 1
        channel.play(sound)

    def shutdown(self):
        if not self.enabled:
            return

        self.stop_drive_loop()
        pygame.mixer.music.fadeout(400)

    def _ambient_volume_target(self):
        return DUCKED_AMBIENT_VOLUME if self.drive_loop_active else AMBIENT_VOLUME
