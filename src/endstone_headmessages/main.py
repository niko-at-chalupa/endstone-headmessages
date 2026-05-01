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
            self.max_messages = cast(int, self.yaml_config.get("max_messages"))
            self.message_decay = cast(int, self.yaml_config.get("message_decay"))
            self.threshold = cast(int, self.yaml_config.get("threshold"))
            self.message_wrapping = cast(bool, self.yaml_config.get("message_wrapping"))
            self.player_name_color = getattr(cf, cast(str, self.yaml_config.get("player_name_color", "RESET")), cf.RESET)
            self.player_name_color_messages = getattr(cf, cast(str, self.yaml_config.get("player_name_color_messages", "GRAY")), cf.GRAY)
        except Exception:
            self.logger.error("Your config is bad! Delete it to generate a new one.")
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
        
        self.server.scheduler.run_task(plugin=self, task=clear_message, delay=self.message_decay)