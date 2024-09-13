from analyzer.signallers.sr_signaller.signal import SRSignal
from fincore.signal_handler import SignalHandler


class SRSignalHandler(SignalHandler):
    def handle_signal(self, signal: SRSignal):
        pass