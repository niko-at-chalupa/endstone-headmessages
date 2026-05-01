from endstone.plugin import Plugin
from endstone.event import event_handler, PlayerChatEvent, PlayerJoinEvent, PlayerQuitEvent
from endstone import Player
from endstone import ColorFormat as cf
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap 
from typing import cast

class HeadMessages(Plugin):
    api_version = "0.11"

    def install(self):
        folder = Path(self.data_folder)
        folder.mkdir(parents=True, exist_ok=True)
        cfg_path = folder / "config.yml"
        self.yml = YAML()
        self.yml.version = (1, 2)
        self.yml.preserve_quotes = True
        defaults = [
            ("max_messages", 4, "Max amount of messages to be shown above a player's head"),
            ("message_decay", 700, "Time (in ticks) before messages go away"),
            ("threshold", 150, "Amount of chars until wrapping/truncation kicks in"),
            ("message_wrapping", True, "Weather to use message wrapping or truncation."),
            ("player_name_color", "RESET", "Player name colour by default (i.e., no messages). Use Endstone ColorFormat colours ( <https://endstone.dev/latest/reference/python/misc/#endstone.ColorFormat> )"),
            ("player_name_color_messages", "GRAY", "Player name colour with messages. Use Endstone ColorFormat colours ( <https://endstone.dev/latest/reference/python/misc/#endstone.ColorFormat> )"),
            ("dynamic_decay", True, "Weather to enable dynamic durations. Minimum duration is the regular message decay."),
            ("ticks_per_char", 1, "ticks/char to be added onto the message decay (20 chars is 20 ticks = 1 second at 20 TPS). If a message is 40 chars (somewhat long) at 1 tick / char and the regular message decay is 700 the decay will be 740 ticks (1 * chars + message decay)")
        ]
        if cfg_path.exists():
            with open(cfg_path, "r", encoding="utf-8") as f:
                existing = self.yml.load(f)
            if not isinstance(existing, CommentedMap):
                existing = CommentedMap(existing or {})
        else:
            existing = CommentedMap()

        for key, default, comment in defaults:
            if key not in existing:
                existing[key] = default
                existing.yaml_add_eol_comment(comment, key)

        with open(cfg_path, "w", encoding="utf-8") as f:
            self.yml.dump(existing, f)

        self.yaml_config = dict(existing)

    def on_enable(self):
        self.player_messages: dict[Player, list[str]] = {}

        self.install()
        try:
            self.max_messages = int(self.yaml_config["max_messages"])
            self.message_decay = int(self.yaml_config["message_decay"])
            self.threshold = int(self.yaml_config["threshold"])
            
            self.message_wrapping = bool(self.yaml_config["message_wrapping"])
            self.dynamic_delay = bool(self.config["dynamic_delay"])
            self.ticks_per_char = bool(self.config["ticks_per_char"])

            p_color = str(self.yaml_config.get("player_name_color", "RESET")).upper()
            self.player_name_color = getattr(cf, p_color, cf.RESET)

            m_color = str(self.yaml_config.get("player_name_color_messages", "GRAY")).upper()
            self.player_name_color_messages = getattr(cf, m_color, cf.GRAY)
        except (KeyError, ValueError, TypeError) as e:
            self.logger.error(f"Configuration error: {e}. Delete your config to generate a new one.")
            return
        self.register_events(self)
    
    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        self.player_messages[event.player] = []
    
    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent):
        self.player_messages.pop(event.player, None)
    
    @event_handler
    def on_player_chat(self, event: PlayerChatEvent):
        player, message = event.player, event.message
        
        if len(message) > self.threshold:
            if self.message_wrapping:
                message = "\n".join(message[i:i+self.threshold] for i in range(0, len(message), self.threshold))
            else:
                message = message[:self.threshold-3] + "..."
        
        if player not in self.player_messages: self.player_messages[player] = []
        self.player_messages[player].append(message)

        if len(self.player_messages[player]) > self.max_messages:
            self.player_messages[player].pop(0)
        
        def update_tag():
            try:
                if player in self.player_messages and self.player_messages[player]:
                    messages_text = "\n".join(self.player_messages[player][-3:])
                    player.name_tag = f"{self.player_name_color_messages}{player.name}{cf.RESET}\n\n{messages_text}"
                else:
                    player.name_tag = player.name
                if player.name_tag == player.name:
                    player.name_tag = f"{self.player_name_color}{player.name}"
            except Exception:
                pass

        update_tag()
        
        def clear_message():
            if player in self.player_messages and self.player_messages[player]:
                self.player_messages[player].pop(0)
            update_tag()
        
        decay = self.message_decay
        if self.dynamic_delay:
            decay = 1 * self.ticks_per_char + self.message_decay
        self.server.scheduler.run_task(plugin=self, task=clear_message, delay=decay)