from endstone.plugin import Plugin
from endstone.event import event_handler, PlayerChatEvent, PlayerJoinEvent, PlayerQuitEvent
from endstone import Player, event
from endstone import ColorFormat as cf

class HeadMessages(Plugin):
    def on_enable(self):
        self.register_events(self)
        self.player_messages: dict[Player, list[str]] = {}

        self.max_messages = 4
        self.message_decay = 700
    
    @event_handler
    def on_player_join(self, event: PlayerJoinEvent):
        player = event.player
        self.player_messages[player] = []
    
    @event_handler
    def on_player_quit(self, event: PlayerQuitEvent):
        player = event.player
        if player in self.player_messages:
            del self.player_messages[player]
    
    @event_handler
    def on_player_chat(self, event: PlayerChatEvent):
        player = event.player
        message = event.message
        if player not in self.player_messages:
            self.player_messages[player] = []
        self.player_messages[player].append(message)

        if len(self.player_messages[player]) > self.max_messages:
            self.player_messages[player].pop(0)
        
        messages_text = "\n".join(self.player_messages[player][-3:])
        event.player.name_tag = f"{cf.GRAY}{player.name}{cf.RESET}\n\n{messages_text}"
        
        def clear_message():
            if player in self.player_messages and self.player_messages[player]:
                self.player_messages[player].pop(0)
            if self.player_messages[player]:
                messages_text = "\n".join(self.player_messages[player][-3:])
                event.player.name_tag = f"{cf.GRAY}{player.name}{cf.RESET}\n\n{messages_text}"
            else:
                event.player.name_tag = player.name
        
        self.server.scheduler.run_task(plugin=self, task=clear_message, delay=self.message_decay)