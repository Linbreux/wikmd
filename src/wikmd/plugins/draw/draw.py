import re
import uuid
from pathlib import Path


from flask import Flask
from wikmd.config import WikmdConfig

default_draw = ('<img title="Click to edit image" onclick="DiagramEditor.editElement(this);" id="" '
                'src="data:image/png;base64,'
                'iVBORw0KGgoAAAANSUhEUgAAAHsAAABACAYAAAA6eggRAAAAAXNSR0IArs4c6QAAA1l0RVh0bXhmaWxlACUz'
                'Q214ZmlsZSUyMGhvc3QlM0QlMjJlbWJlZC5kaWFncmFtcy5uZXQlMjIlMjBtb2RpZmllZCUzRCUyMjIwMjMt'
                'MDEtMTBUMjMlM0EwOCUzQTE1LjYwOVolMjIlMjBhZ2VudCUzRCUyMjUuMCUyMChYMTElM0IlMjBMaW51eCUy'
                'MHg4Nl82NCklMjBBcHBsZVdlYktpdCUyRjUzNy4zNiUyMChLSFRNTCUyQyUyMGxpa2UlMjBHZWNrbyklMjBD'
                'aHJvbWUlMkYxMDguMC4wLjAlMjBTYWZhcmklMkY1MzcuMzYlMjIlMjBldGFnJTNEJTIyYnZnWWFEa2ZIcjdp'
                'dVRJYVRtR2slMjIlMjB2ZXJzaW9uJTNEJTIyMjAuOC4zJTIyJTIwdHlwZSUzRCUyMmVtYmVkJTIyJTNFJTND'
                'ZGlhZ3JhbSUyMGlkJTNEJTIyZW1ZUlNERFJrRFAyWWQzRVp5M3IlMjIlMjBuYW1lJTNEJTIyUGFnZS0xJTIy'
                'JTNFalpQTmJvUWdFSUNmeHZzcVcyT3Z0ZHZ0cFNjUFBWT1pDbGtVZzdocW43NGd3eW94VFhyUm1XOWclMkZr'
                'bEkyYzVYVFh2JTJCb1JqSUpEdXhPU0d2U1phbFJWcllueU9MSndWNThxRFJnbmwwMmtBbGZnQnZCam9LQmdN'
                'eWo0eFMwb2clMkJoclhxT3FoTnhLaldhb3FQZlNzWlIlMkIxcEE5RUpCNnFheWlQOUZNeHdyQ0xMTiUyRjRP'
                'b3VFaGNwbyUyRmU4c1hyVyUyQk5WbU9IOFRyVmdiZTBOTGpCSEFaT21acDJpRndTVW1xbGpKZmF1UVRwMmhw'
                'MzdPMFBLNlk4bUNVVUVYTFYwSmwlMkZlUWhGM0trYzBVY3BSWDJ6aUlPR2RRajJBMHdZSjNOSG1LQ05wdTBo'
                'JTJCTVNGZ2FxbnRkTW51eVVKZWVHbWxWWkxyZmdvM2lscnY0Q2hka3diUzd1RE5qRHZFSlp4QmRXQzBZczln'
                'bFp5UHZzclM3eFcwemJMTkl5QjclMkJhWUk2TzRQczNEODlZMksyRG5ncnFOYkxYdG5nUzUlMkZBSSUzRCUz'
                'QyUyRmRpYWdyYW0lM0UlM0MlMkZteGZpbGUlM0WwqEjDAAAPNklEQVR4Xu1dCXBURRPuXeMSYgIJ4ReCAfFA'
                'IT8pFAWPEgUpCQWxEki8C4L8KES0kuIQvC9ADg0JqKE8IAEtf0tAkCiHBwIqVIEHSbhBOfQPUXKRGMISN399'
                'nX3J7PF25719L9mAUwWE3Zme7v66e3qmJ+9ZyGuzXGu1WsZERUWlVFdX97Tb7aFKNwsRNXgZo/Y5d/X5pXcO'
                '1D/VTkz7CK08+ehv1OQiHeFnm81WFxERcbSiomKVw+FYQUQHPLhx9sc/Li08PDy3vr5+fHp6uiUpKenifv36'
                'UWRkpIHSC6RgNZZG4/FgxJwZg46qLtmFQZWVlbR7925au3btudzc3IaQkJClNTU16d4EFXXcLTo6+qvEkYk9'
                'snOyw9QAFpnTxWjQqdvT+HSx6KGMQLTjZawEOQCfmZlZW1BQcLysrGwokeV/YhxuAjs6OnpfZmZm72effVaX'
                'rOfrIAkdB53os2bNouzs7P1lZWV9ROYYbITulJSUsXl5eWGenLdFcQPRfxuQV4LFtLS0M6tXr84XQzrAvjY0'
                'NLSwpKTEpn9tlpg9EP07k0KLzDQyfWR4kaEj00dmLhP6IKTHxMScq6ur609ExZwnW63WWRkZGU9mZWVdHPCc'
                'BgtvMLmAxdNPQIMkGrr642fKlCn1OTk5KxwOx3gGG2v1qlWret9xxx3+xv7zfVvSQAPRlq1baPTo0cfKy8vv'
                'IqJDFpvNdqa0tDQ0MrKjsAGSMa82nJfLiBcIsNL0XTtKD/PJWzMVhPIuXbrY7XY7wN7F2+2GBm/HJP6kNYY1'
                'f7O09vdtXUqLhXNwhO0TmsFm4Y3SgFF0WtsiTJ4/EDU5wR5MRLWawfYuVyDsqGnKDJomo2I0eTUVaFCNALZD'
                'BWwva4mGCYyRWeuEWvsbw6UvKi3OkZcJBbAbSxT61mzzlRXwDCZq20TSAYstEggCsA3OQs3WvB/6Zk8fCPqt'
                'C7aHZoxSlVY6WvsHonKdYzWwqNaVwbbQYJQWWzSMe2dIg0Q6dXa+DpPRnIpnywxtIbVJsyLdUUPRXAPNFlKH'
                'OA1z52RRhlPpMP7555/Tyy+/zMXxsLAwwpHq/Pnz6eqrr6aff/6ZUlNT6fDhw/Taa6/R/v376d1331UVH0WW'
                '4uJiio2NVe3zxhtv0I4dO+j9999vETXm5eXRuHHjTJlLTT9ffvkl9e7d26semvlpoM6d/8W6gK4Daaqe3UCW'
                'phsjBQUF9OCDD9LChQspOTmZ6uvrKSsri8AQgD127FgT2LW1tfx9hw4dmC9vFtcSYP/999900UUXSekGO5CY'
                'mBg6efKkVH/ZTorsItiifpKSkuipp56im2++2YWkOz+dO3c2E2xXca677joaM2YMTZ061eWL9957jxITE6mk'
                'pIRSUlPpiJtn79mzhyZMmEAnTpygK6+8kvLz8+mKK67gq01FxcXUPTaWnnnmGSosLMRVGrJarU304dnfffcd'
                'AbRvv/2WunbtSp988gldfvnldPDgQXr00UcZnPDwcFq0aBHdeuut9OOPP9L48eOpb9++9Pvvv9PmzZvps88+'
                'Y4Xa7XbmATwDWLGNGjWK54+Li6P169cTzpEnTZpEf/75J7ULDaU5s2fT3Xff7YGxGh/o+Oqrr1Jubi516tSJ'
                '7rnnHlq2bJlL5OvVqxe98MILdNlll9GCBQtQpGii787P9ddfz1H1rbfeYl0Dh6effpr7y8inEPYbxquqqhic'
                'o0ePsqK9NW9h6p133iHcWXvppZcIzM+fP4++/nozbdiwgekhjAPMefPm0datWxk0sQFsKANA9+nThyMLDGX2'
                '7NnUv39/Sk9Pp0ceeYR27dxJScnJ9Ouvv9KBAwfolltuYUDvu+8+NgaM3bZtGxvA66+/znOuXr3aZa5Tp05x'
                'KK2rqyOHw8F9n3vuOXrggQcIBgtDOnLkMIfTxtbosyIfO3fu5KgHPo4cOcJj9u3bh+IDOwrCsPsyh3mw3Cme'
                'rUQCkR/MBs++//77afHixWzo8fHxbJCnT5+Wks8FbF/Z+PHjxxnkM2fOUGhoqNew7A1sKAtggym0c+fO0dmz'
                'ZxlUgJ2/fDlNmzqVvvnmG7Zu9wawN23aRJ9++ikrd9GixfTDDz/QK6+8wh4IQZVIMGDAAM4VoqOjaeDAgVRT'
                'U8PfLV++nD788EP2VjR8HhUVxaCKIV5ULoBCJAN9pyewAc2cOZMQdpUGvcT1iaPT1Z58AGTMiWiBtnHjRpo8'
                'ebJfsBXa3sCGLmBcaIgW0AWMWEY+ac/+66+/KCI8nA4eOqSaIHgDe+KkiZSaksrruXsD2EjyIiIiOLkLbd/e'
                '40ape4Km/D8zM5M9QUzuwCNCJpKdhIQEDuFoMIAXX3yRPUNpp6uqaO++fbwseFPu9u3b2YtEvkeOHMnRCUuS'
                '0nbt2qXKB7wPf5bl5bFc8HpECX+e7QtsMUFT1vA1a9Z4yIdIDGMT5ZMGGx3hORAYihMbwuy9997LXuuejcOz'
                'EaYwObwMa+Yvv/zCgABsMIoQBm/Mycnx6tliNs5gb99Bc+fNZbpKxBAHYmkYPnw4/fbbb/wxMvmVK1fyXL6a'
                'N89W+Ma4m266iXD5Uly3MYcaH7lLcmnjho1N8yLBhZEaDTb0IyOfJrC/+OILDmFz585lq0dDNv7RRx9xcoXQ'
                '5w421uz4+L40bdp03tIAUIS2Des3UGRU45oN78b688EHH9Dgwai8NTc1zwaAN9xwA02bNo29BUlURkYGvf32'
                '25xXKGBj/fvjj1KK7xvP6zQSInjYihUrOKETG4CF0eFf8AQQkTgiT0DkGTp0KAOFJUBsanxAH0OGDOH1/tJL'
                'L+X8AXTcwUbihURueMLw5svyDURVp5v5ueSSSzgyeXr2doqI6MD68yefJrDRGXtCJFs//fQTr91QKvbZ3bp1'
                'U91nFxUV04QJ/+GQeM0117hk48o+G2sywCosKqSI8IgmXfoCGyFy4sSJnOUjakyZMoWzZ3fPBjElW8WWB8sG'
                'kpzbbrvNw9GHDRvG2TzOE9q3b8/04PH4GdnyXXfhgodrU+MDvZ5//nmCwXfs2JFpZWdnszGK5xDIsJE04rrv'
                'E0884UJc5GfEiBFewG7cdzfKN5Nqa8/4lA/EfWfjMscyPgOk+pcypGX66Jxe5QRAPzXTRxqgDL9bL9OFkJzA'
                'AFklZ5Lp5oUbQ4s6MtLK9HGVxQVs/KqVQ+sdNO1zymjzAuxjviLbjGcbg77BCjWYXLOM5hAOgqqXOYIZYxyB'
                'UJGTS66XFj7UKV5gnu2qNEOXWS14tFJfw8A23kJFjXhSV87Xcf6NvT/2sIY2cwUylFVZYoaBLTuhUf0UsHEs'
                'iNM08UhU7xxayqJa59BlO7oGqXMWONhqDMnsTjRoDMWExx9/nAsYDz30EJ/gFRUVcWVL8WzUgXHAsnbtGnI4'
                'GvhUDkeyISEhXFTBePyMAxkcCOHkqby83KMsigIKqms4Bu7RowefunXv3p1PAXESdvZsHRUX7+HPUH178803'
                '+Swcx8mocGluTl0ZjK0HG/JgG8WJBuNQuIXHQelLly6lhIRhlJu7hIHDyVwz2Ido3boCrk6hIgTBUAFDLRv1'
                'ZFTuUPpEoQSgAEyUIysqKlzKogAfVTgcdaL+DcMArSVLlhBO9ebMmUN79+7l06qePXsyPRgUyrSoseMyh7HP'
                'CjFK8f5O0DSbqMqAAPmFAlHpUoofKFHiGBPHpe6ejQqYUhsHUAA5JSWFAQWQaBiDCwwYD5piWRTfV1dXM5ho'
                'KCHi4gEiA8DesmULffzxx/zdoEGD+JgTxSBU2uLi/k1VVY0l3dZrorJdFd/ynq1DC99//z0XJXC2rDQUCHBZ'
                'QQQbRZHp06dziQ+CoT8iwJ133kljx451SeLatWvHBRyALZZFcXkBno9lAw2ej6iC2gDARmkT17HQsEygIIPb'
                'OuADZ9WomQdrkwe7FSUAePBMxbOhUHieu2fDk3FBAuEaazvqzwi1qEUDGBgDWmlpKdd7Fc8Wy6LwZIRqXAxA'
                'EogqG8B1Bxs+M6QlwTYgB5IC2+z9qL8oj0QJ6ygSJwCDyhHWZniu6Nkos8IocEcLt2ABMkIsqnUxXWNozdo1'
                'dPvtt3P5Egka1mwYkAg2vBdevW7dOvZqrPcwLpQY9Xu2Pwn1eZJWqlJge7CidRZdsrhOgis+uACAjBsei5sp'
                'yKZRhlSycYR7hGubzUYDBg6kUcnJ9PDDD7ORYC2fMWMGe+tjkx+jGU/O4CQMgIpgw/txSaG8rJxiu8dyvRl3'
                'y3CREet88Ifx8+oETZ+lKb+wCOtGdo81G/fMcFnhQmn6PFtGO/owkaGsq8+NN97IWyP8wZVm7NMR6i+kZh7Y'
                'QaZFhHjcGMHVI1wVwjUmXAsKuubHSdQ3Vv4lMQVs7/ya7epm0/evzGDvEdBvcQaiXumx3FH7vkMb/eCASZpn'
                'J7ta+5vi2cGhuiDkQis6Rp2ZO+mYDrZW+RgiXYOCAVyjGDeKjqtOTAc7GCAwlAdzcDCUxWZirumcxcK/OMkX'
                '9Fv0yQvGS6czT21V8LRPrn1Es6YvYM/WrjbtI4w36UAouoDd/OxStVdDtHVxA1FVYGNbW3PCs0uHcRjX9lRi'
                '9e1QawsWGCzBMdpoHaIO73wqcRqD7fG8caNnDA49BpbtB7NOfPDmfN74fx0OBz/sRuVNAjLSyfQJFqTPHz5k'
                'U1LhTQJ4sPwJIuJnl/I7QkaPHj0uPz+/6f1dbUM9xhmcNkraereGLtPS0upWrly5qba2Nss5Pz+VmFt0dPTh'
                'zMzMq8x7+48BCjKAhKj4gMlpJaC1v04rwa8DL1y4EG8Q4LXaeWTFzxtX2lWdOnX6KjExsUtOTk6o/pfD+OGw'
                'hQTWqacmzci/VC54BELozsjIqCsoKCgtLy/HY65OCWDzmwTE1issLGyBw+EY4XxjX0hgb+zTqgj1/mrfaJ0h'
                'ECPwGNuqkzdyU1lRSbsL+Y199Xhjn9VqXS+EbnRxkIVOUgMd8mbAA/D6J6vVmhAZGTmopqYmxm632/QpyagX'
                'Ueqb/UIYZbPZ7OHh4SWVlZXbHA4HrsciGRNbLZ7ngw9cwHZCA2D7ERGSteYn0klrrq0ArIFPDV2l1WR+RwcR'
                '1RERrubYPcBunp+l60VEymMB5Zcw84X4ZwYvGhDsEYsLWgle7yR29QcibuZ1wQP39Hu6f2y0OY623r7e56yV'
                'kn9JWqEHC8F/KZ6MpKyULFTb9IxxJ1v/Bw2R64jwecc8AAAAAElFTkSuQmCC" '
                'style="">')


class Plugin:
    @staticmethod
    def import_head():
        return "<script type='text/javascript' src='/static/js/drawio.js'></script>"

    def __init__(self, flask_app: Flask, config: WikmdConfig, web_dep):
        self.name = "DrawIO integration"
        self.plugname = "draw"
        self.flask_app = flask_app
        self.config = config
        self.web_dep = web_dep
        self.save_location = Path(self.config.wiki_directory) / ".plugin-draw"
        config.hide_folder_in_wiki.append(".plugin-draw")
        self.save_location.mkdir(exist_ok=True)

    def get_plugin_name(self) -> str:
        """
        returns the name of the plugin
        """
        return self.name

    def process_md(self, md: str) -> str:
        """
        returns the md file after process the input file
        """
        return self.search_for_pattern_and_replace_with_uniqueid(md)

    def process_html(self, html: str) -> str:
        """
        returns the html file after process the input file
        """
        return self.search_in_html_for_draw(html)

    def communicate_plugin(self, request):
        """
        communication from "/plug_com"
        """
        id_ = request.form['id']
        image = request.form['image']

        self.flask_app.logger.info(f"Plug/{self.name} - changing drawing {id_}")

        # look for folder
        location = self.save_location / id_
        if not location.exists():
            return "ok"
        with location.open("w") as fp:
            fp.write(image)

    def look_for_existing_draw_id(self, draw_id: str) -> str:
        """
        look for a drawId in the wiki/draw folder and return the file as a string
        """
        location = self.save_location / draw_id
        if not location.exists():
            self.flask_app.logger.info(f"Plug/{self.name} - Could not find file with ID %s", draw_id)
            return ""

        with location.open() as fp:
            data = fp.read()
        return data

    def create_draw_file(self, filename: str) -> None:
        """Create a default drawing at filename"""
        location = self.save_location / filename
        with location.open("w") as fp:
            draw = default_draw.replace('id=""', f'id="{filename}"')
            fp.write(draw)

    def search_for_pattern_and_replace_with_uniqueid(self, md: str) -> str:
        """
        search for [[draw]] and replace with draw_<uniqueid>
        """
        filename = "draw_" + str(uuid.uuid4())
        result = md.replace("[[draw]]", f"[[{filename}]]")
        self.create_draw_file(filename)
        return result

    def search_in_html_for_draw(self, html: str) -> str:
        """Search for [[draw_<unique_id>]] in the html string and replace it
         with the content of a corresponding drawfile
        """
        draws = re.findall(r"\[\[(draw_.*)]]", html)
        result = html
        for draw in draws:
            result = re.sub(fr"\[\[{draw}]]", self.look_for_existing_draw_id(draw), result)
        return result
