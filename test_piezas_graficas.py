import unittest

from PIL import Image

from piezas_graficas import limpiar_artefactos, preparar_pieza, recortar_fotograma


class PiezasTests(unittest.TestCase):
    def test_recorte_elige_solo_un_cuadro_y_elimina_margenes_transparentes(self):
        hoja = Image.new("RGBA", (100, 40), (0, 0, 0, 0))
        hoja.paste((230, 20, 10, 255), (4, 5, 16, 35))
        hoja.paste((10, 100, 210, 255), (55, 4, 95, 36))
        fotograma = recortar_fotograma(hoja, 2, 1)
        self.assertEqual(fotograma.size, (12, 30))
        self.assertEqual(fotograma.getpixel((0, 0)), (230, 20, 10, 255))

    def test_negras_en_grises_y_blancas_en_color(self):
        imagen = Image.new("RGBA", (12, 20), (230, 20, 10, 190))
        blanca = preparar_pieza(imagen, 80, True)
        negra = preparar_pieza(imagen, 80, False)
        self.assertEqual(blanca.size, (80, 80))
        pixel_blanco = blanca.getpixel((40, 40))
        pixel_negro = negra.getpixel((40, 40))
        self.assertNotEqual(pixel_blanco[0], pixel_blanco[1])
        self.assertEqual(pixel_negro[0], pixel_negro[1])
        self.assertEqual(pixel_negro[3], 190)

    def test_limpieza_conserva_personaje_y_elimina_ruido_aislado(self):
        imagen = Image.new("RGBA", (24, 24))
        imagen.paste((210, 120, 120, 255), (7, 7, 19, 21))
        imagen.putpixel((8, 8), (255, 0, 0, 255))
        imagen.paste((250, 250, 250, 255), (0, 0, 2, 2))
        limpia = limpiar_artefactos(imagen)
        self.assertEqual(limpia.size, (12, 14))
        self.assertEqual(limpia.getpixel((1, 1))[3], 0)
        self.assertEqual(limpia.getpixel((10, 10))[3], 255)


if __name__ == "__main__":
    unittest.main()
