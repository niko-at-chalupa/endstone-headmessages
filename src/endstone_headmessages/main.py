from endstone.plugin import Plugin
from endstone.event import event_handler, PlayerChatEvent, PlayerJoinEvent, PlayerQuitEvent
from endstone import Player, event
from endstone import ColorFormat as cf

class HeadMessages(Plugin):
    def on_enable(self):
        self.register_events(self)

        self.player_messages: dict[Player, list[str]] = {}

    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        player = event.player
        self.player_messages[player] = []

    @event_handler
    def on_player_chat(self, event: PlayerChatEvent):
        player = event.player
        message = event.message
        
        if player not in self.player_messages:
            self.player_messages[player] = []
        self.player_messages[player].append(message)
        
        messages_text = "\n".join(self.player_messages[player][-3:])
        event.player.name_tag = f"{cf.GRAY}{player.name}{cf.RESET}\n\n{messages_text}"
        
        def clear_message():
            if player in self.player_messages and self.player_messages[player]:
                self.player_messages[player].pop()
                if self.player_messages[player]:
                    messages_text = "\n".join(self.player_messages[player][-3:])
                    player.name_tag = f"{cf.GRAY}{player.name}{cf.RESET}\n\n{messages_text}"
                else:
                    player.name_tag = player.name
        
        self.server.scheduler.run_task(plugin=self, task=clear_message, delay=700)