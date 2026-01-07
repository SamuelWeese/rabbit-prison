from PyQt5.QtGui import QPixmap

class SpriteCache:
    _sprites = {}

    @staticmethod
    def load():
        # Blocks
        SpriteCache._sprites["water"] = QPixmap("assets/water_block.png")
        SpriteCache._sprites["grass"] = QPixmap("assets/.png")
        SpriteCache._sprites["wall"] = QPixmap("assets/wall_block.png")
        SpriteCache._sprites["fence"] = QPixmap("assets/fence_block.png")
        SpriteCache._sprites["food"] = QPixmap("assets/food_block.png")

        SpriteCache._sprites["farm0"] = QPixmap("assets/farm_0.png")
        SpriteCache._sprites["farm1"] = QPixmap("assets/farm_1.png")
        SpriteCache._sprites["farm2"] = QPixmap("assets/farm_2.png")
        SpriteCache._sprites["farm3"] = QPixmap("assets/farm_3.png")

        # Rabbit
        SpriteCache._sprites["rabbit_default"] = QPixmap("assets/rabbit_default.png")
        SpriteCache._sprites["rabbit_sleep"] = QPixmap("assets/rabbit_sleep.png")
        SpriteCache._sprites["rabbit_standing"] = QPixmap("assets/rabbit_standing.png")
        SpriteCache._sprites["rabbit_hop"] = QPixmap("assets/rabbit_hop.png")
        SpriteCache._sprites["rabbit_jump"] = QPixmap("assets/rabbit_jump.png")
        SpriteCache._sprites["rabbit_rizz"] = QPixmap("assets/rabbit_rizz.png")
        SpriteCache._sprites["rabbit_preach"] = QPixmap("assets/rabbit_preach.png")
        SpriteCache._sprites["speech_bubble_0"] = QPixmap("assets/speech_bubble_1.png")
        SpriteCache._sprites["speech_bubble_1"] = QPixmap("assets/speech_bubble_1.png")

    @staticmethod
    def get(name):
        return SpriteCache._sprites.get(name)
