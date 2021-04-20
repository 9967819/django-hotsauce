from gazpacho.interfaces import IReferencable

class ReferenceContainer:
    """This class is intended to be used by gadgets to keep track of
    objects that keeps references to it.

    The objects that keep references to the gadgets are called
    referrers.  When the gadget is remvoed in some way the reference
    container makes it possible to update all of these referrers and
    clear the references. In the same way, when the removal is undone
    the references can be restored.

    When a referrer adds a reference to the gadget it should add
    itself to the reference container for that gadget. When the gadget
    is deleted or a deleted gadget is restored the contaner will make
    sure that the appropriate methods are called on the referrer. The
    referrer has to implement the IReferencable interface.
    """

    def __init__(self, gadget):
        """Initialize the reference container for a specific gadget.

        @param gadget: the gadget
        @type gadget: L{gazpacho.gadget.Gadget}
        """
        self._gadget = gadget
        self._referrers = []

    def clear_references(self):
        """Clear all references to this gadget.

        This method should be called when the gadget is deleted.
        """
        for referrer in self._referrers:
            referrer.remove_reference(self._gadget)

    def restore_references(self):
        """Restore all references that have previously been cleared.

        Should be called when a deleted gadget is restored.
        """
        for referrer in self._referrers:
            referrer.add_reference(self._gadget)

    def add_referrer(self, referrer):
        """Add a referrer, i.e. the one that referres to the gadget
        represented by this container.

        The has to implement the IReferencable interface which
        provides methods for removing and restoring the reference to
        the gadget.
        
        @param referrer: the object that referres to the gadget
        @type referrer: L{gazpacho.interfaces.IReferancable}
        """
        if not IReferencable.providedBy(referrer):
            raise TypeError("%s should be implementing %s" % (referrer, IReferencable))
        self._referrers.append(referrer)

    def remove_referrer(self, referrer):
        """Remove the specified referrer from the reference container.

        @param referrer: the object that referres to the gadget
        @type referrer: L{gazpacho.interfaces.IReferancable}
        """
        self._referrers.remove(referrer)
