from __future__ import unicode_literals, absolute_import, print_function, division

from core.management.commands import CommunityCommand


class Command(CommunityCommand):
    """
    Continuously polls a Community until it's completely grown.
    """

    def handle_community(self, community, **options):
        community.config = {"async": False}
        community.clean()
        community.save()
        community.grow()
        print("Result:", community.kernel)
        print("Growth:", [growth.id for growth in community.growth_set.all()])
