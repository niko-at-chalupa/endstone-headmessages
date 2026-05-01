from endstone.plugin import Plugin
from endstone.event import event_handler, PlayerChatEvent, PlayerJoinEvent, PlayerQuitEvent
from endstone import Player
from endstone import ColorFormat as cf

class HeadMessages(Plugin):
    def on_enable(self):
        self.register_events(self)
        self.player_messages: dict[Player, list[str]] = {}
        self.max_messages = 4
        self.message_decay = 700
        self.threshold = 150
        self.message_wrapping = True
    
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
            if player in self.player_messages and self.player_messages[player]:
                messages_text = "\n".join(self.player_messages[player][-3:])
                player.name_tag = f"{cf.GRAY}{player.name}{cf.RESET}\n\n{messages_text}"
            else:
                player.name_tag = player.name

        update_tag()
        
        def clear_message():
            if player in self.player_messages and self.player_messages[player]:
                self.player_messages[player].pop(0)
            update_tag()
        
        self.server.scheduler.run_task(plugin=self, task=clear_message, delay=self.message_decay)
        print(event.player.name_tag)