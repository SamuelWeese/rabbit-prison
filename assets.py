from PyQt5.QtGui import QPixmap

class SpriteCache:
    _sprites = {}

    @staticmethod
    def load():
        SpriteCache._sprites["water"] = QPixmap("assets/water_block.png")
        SpriteCache._sprites["grass"] = QPixmap("assets/.png")
        SpriteCache._sprites["wall"] = QPixmap("assets/wall_block.png")
        SpriteCache._sprites["fence"] = QPixmap("assets/fence_block.png")
        SpriteCache._sprites["food"] = QPixmap("assets/food_block.png")
        # Farm
        SpriteCache._sprites["farm0"] = QPixmap("assets/farm_0.png")
        SpriteCache._sprites["farm1"] = QPixmap("assets/farm_1.png")
        SpriteCache._sprites["farm2"] = QPixmap("assets/farm_2.png")
        SpriteCache._sprites["farm3"] = QPixmap("assets/farm_3.png")

    @staticmethod
    def get(name):
        return SpriteCache._sprites.get(name)
