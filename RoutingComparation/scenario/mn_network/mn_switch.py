from mininet.node import OVSSwitch

# Create a custom OVSSwitch subclass with STP enabled
class STPOVSSwitch(OVSSwitch):
    def __init__(self, *args, **kwargs):
        kwargs['stp'] = True
        OVSSwitch.__init__(self, *args, **kwargs)
