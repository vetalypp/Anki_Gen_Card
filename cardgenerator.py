# -*-coding:utf-8-*-

from aqt import mw
import codecs
import re
from subprocess import Popen, PIPE
from urllib import request
from PyQt5 import QtGui
from anki.importing import TextImporter
from aqt.qt import *
from aqt.utils import showInfo, showText, tooltip
from bs4 import BeautifulSoup
from . import wi
from .log import logger
import time
logger.info(time.asctime( time.localtime(time.time()) ))

def pos(fn):
    def wrapp(*argv):
        return "<section class='pos'>" + fn(*argv) + "</section>"

    return wrapp


def defen(fn):
    def wrapp(*argv):
        return "<section class='def'>" + fn(*argv) + "</section>"

    return wrapp


def exa(fn):
    def wrapp(*argv):
        return "<section class='exa'>" + fn(*argv) + "</section>"

    return wrapp


class ParsEn:
    def __init__(self):
        self.domaine = "https://dictionary.cambridge.org/"
        self.main_domain_stat = 'https://dictionary.cambridge.org/dictionary/english/'
        self.hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}  # для страницы
        opener = request.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)')]  # для скачиваня mp3
        request.install_opener(opener)
        self.notfound = None
        self.download_mp3 = None

    @pos
    def getpos(self, group):
        try:
            pos = group.find("span", "pron dpron").span.text
            logger.debug('getpos ok')
        except Exception as e:
            logger.warning(e)
            pos = ''
        return pos

    @defen
    def getdef(self, group):
        try:
            defen = group.findAll("div", "ddef_h")[0].text
            logger.debug('getdef ok')
            return defen[:-1]
        except Exception as e:
            logger.warning(e)

    @exa
    def getexa(self, group):
        try:
            exa = group.find_all("div", "examp dexamp")[0].text
            logger.debug('getexa ok')
        except Exception as e:
            logger.warning(e)
            exa = ''
        return exa

    def getmp3(self, page, word):
        try:
            pat = re.compile("\s\w+\W+(.*)\W\s")
            page = page.source
            url_mp3 = str(pat.findall(str(page))[0])
            mp3_name = str(word) + '.mp3'
            request.urlretrieve(self.domaine + url_mp3, mp3_name)
            logger.debug('getmp3 ok')
        except Exception as e:
            logger.warning("Error geting mp3: " + str(e))

    def get_image(self, page, word):
        pat = re.compile("\W\s\W\w+\W+(.+\d*)\W\s\}\s\W\s*")
        try:
            chank = str(page.find('div', "dimg").script)
            img = pat.findall(chank)[0]
            img_name = str(word) + '.img'
            request.urlretrieve(self.domaine + img, img_name)
            logger.debug(img)
            img_name = "<img src={}>".format(img_name)
            return img_name
        except:return " "

    def getword(self, page):
        try:
            word = page.title.text[:-46].lower()
            logger.debug('getword ok')
            return word
        except:
            result = page.find('strong', {'class': 'pageTitle'})
            if result:
                word = result.getText()
                return word

    def getpron(self, page):
        try:
            pron = page.find("span", "pron dpron").span.text
            logger.debug(u"pron ok ")
            return pron

        except Exception as e:
            logger.warning(e, exc_info=e)
            return ''

    def assemble_def(self, page):
        out = ''
        word = self.getword(page)
        logger.debug('asemble: ' + word)
        if self.download_mp3:
            self.getmp3(page, word)
            mp3_name = '[sound:' + word + '.mp3'']'
        else:
            mp3_name = ' '
        if word == None:
            return
        else:
            word += ';' + self.getpron(page) + ';' + self.getdef(page) + ';' + mp3_name + ';' + self.getexa(page) + ';' \
                   + ';' + self.get_image(page, word) + '\n'
            out += word
        return out

    def run(self, i):
        req = request.Request(self.main_domain_stat + i.upper(), headers=self.hdr)
        try:
            response = request.urlopen(req)
            page = BeautifulSoup(response.read(), 'html.parser')
        except UnicodeEncodeError:
            logger.debug(i + ' is not english word')

        try:
            # page.title.text[:-46].lower()
            if page.title.text[-45] == '|':
                valid = True
            else:
                valid = False
        except:
            valid = False
        if valid:
            return self.assemble_def(page)
        else:
            return None

class Logger(object):

    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout
        self.log = codecs.open(filename, 'w', encoding='utf-8')

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)


class Cardgenerator_wi:

    def __init__(self):
        #path = os.path.dirname(os.path.abspath(__file__))
        self.card = None
        self.cards = ''
        self.lang_default = True
        self.notfound = None
        self.fileName_output = os.path.expandvars('%temp%') + '\\gencard.txt'
        self.words = None
        self.action_default = True
        self.window = QDialog()
        self.ui = wi.Ui_dialog()
        self.ui.setupUi(self.window)
        self.deck = self.ui.comboBox_2.currentText()
        self.ui.comboBox.addItems([u'Английский', u'Румынский'])
        self.ui.comboBox_2.addItems(sorted(mw.col.decks.allNames()))
        self.ui.comboBox_3.addItems(["mybase_en"])
        self.ui.comboBox_3.addItems(mw.col.models.allNames())
        self.ui.comboBox_4.addItems([u'Импортировать', u'Открыть без имп.'])
        self.ui.pushButton.clicked.connect(self.setOpenFileName)
        self.ui.pushButton_2.clicked.connect(self.setOpenFileName_2)
        self.ui.pushButton_4.clicked.connect(self.main)
        self.ui.comboBox.activated.connect(self.combo_chosen)
        self.ui.checkBox.setChecked(True)
        self.ui.comboBox_4.activated.connect(self.combo_chosen_action)
        self.ui.toolButton.clicked.connect(lambda: self.clear(1))
        self.ui.toolButton_2.clicked.connect(lambda: self.clear(2))

    def clear(self, wind):
        if wind == 2:
            self.filename_txt = None
            self.ui.pushButton.setText('...')
            return self.filename_txt
        else:
            self.filename_kindle = None
            self.ui.pushButton_2.setText('...')
            return self.filename_kindle

    def setOpenFileName(self):
        self.filename_txt = QFileDialog.getOpenFileName(caption=u'Открыть cписок', filter='*.txt',
                                                        directory='C:\\Users\\user\\Desktop\\')[0]

        logger.debug('Set txt file ' + self.filename_txt)
        if self.filename_txt:
            name = os.path.split(self.filename_txt)
            self.ui.pushButton.setText(name[1])

    def setOpenFileName_2(self):
        self.filename_kindle, f = QFileDialog.getOpenFileName(caption=u'Открыть файл kindle', filter='*.txt',
                                                              directory='C:\\Users\\user\\Desktop')
        logger.debug('Set kindle file ' + self.filename_kindle)
        if self.filename_kindle:
            path = self.filename_kindle
            name = os.path.split(path)
            self.ui.pushButton_2.setText(name[1])

    @property
    def run(self):
        out = ''
        c = 0
        card = 0
        self.ui.progressBar.setRange(0, len(self.words))
        logger.debug(str(self.words) + str(len(self.words)))
        self.parser = ParsEn()
        self.parser.download_mp3 = self.ui.checkBox.checkState()
        for item in self.words:
            try:
                result = self.parser.run(item)
                if result:
                    out += result
                else:
                    self.ui.textEdit.moveCursor(QTextCursor.End)
                    if not self.notfound:
                        self.ui.textEdit.insertPlainText(u" не найдено:\n")
                        self.notfound = 1
                    self.ui.textEdit.insertPlainText(" %s   \n" % (item[:-1]))
                c += 1
                card += 1
                self.ui.progressBar.setValue(c)
                QtGui.QGuiApplication.processEvents()
                logger.debug(str(c)+ " : " +str(len(self.words)))
            except Exception as e:
                logger.warning("Got an exeption {}".format(e), exc_info=e)

                # break

        tooltip(u'Генерированно: %d карт из %d ' % (card, c))
        return out
        # self.cart.write(out)

    def streap(self, kindle_notes):
        pat = re.compile('\w+', re.UNICODE)
        words = []
        try:
            logger.debug(kindle_notes)
            #words.append(['%s%s' % (kindle_notes[2].strip(),\
                     #kindle_notes[i + 3].strip()) for i in range(0, len(kindle_notes), 5)])
            for i in range(0, len(kindle_notes), 5):
                word = '%s%s' % (kindle_notes[2].strip(), kindle_notes[i + 3].strip())
                try:
                    item = pat.findall(word)[0]
                    words.append(item)
                except IndexError:
                    pass

        except Exception as a:
            logger.debug(a[0])
            if a[0] == 'list index out of range':
                logger.debug(a[-6:])
                logger.debug("Exeption of sreap" + str(a))
                # logger.debug kindle_notes
                kindle_notes.pop(0)
                # logger.debug kindle_notes
            self.streap(kindle_notes, words)
        logger.debug(words)
        logger.debug(len(words))
        return words

    def gen_ro(self, words):
        pat = re.compile('\w+', re.UNICODE)
        c = 0
        card = 0
        out = ''
        toal_words = len(words)
        self.ui.progressBar.setRange(0, toal_words)
        logger.debug(words)
        for i in words:
            c += 1
            i = pat.findall(i)[0]
            logger.debug(str(c) + ":" + str (len(words)))
            self.ui.progressBar.setValue(c)
            QtGui.qApp.processEvents()
            try:
                main_domain_stat = 'http://m.dexonline.ro/definitie/'
                page = BeautifulSoup(request.urlopen(main_domain_stat + i))
                defen = page.find('span', {'class': 'def'})
                wor = str(defen.b.string)
                try:
                    tran = str(defen.i.string)
                except:
                    tran = '-'
                try:
                    if wor == 'None':
                        defen.sup.replaceWith('')
                        wor = defen.b.renderContents()
                except Exception as e:
                    logger.warning(e)
                try:
                    if tran != 'None':
                        defen.i.replaceWith('')
                        tran = tran.replace(',', '')
                    else:
                        tran = '-'
                except Exception as e:
                    logger.warning(str(e))

                wor = wor.replace(',', '')
                defen.b.replaceWith('')
                defen_text = str(defen)
                defen_text = defen_text.replace("&#x2013;", "-").replace("&#x2666;", "x2666").replace("&#x25ca;",
                                                                                                      "x25ca").replace(
                    '\n', "").replace('<b>', '</br>').replace('</b>', '').replace('\t', ''
                                                                                  ).replace(
                    '<span class="def" title="Clic pentru a naviga la acest cuvânt">', '')
                wor += ' \t ' + tran + '\t' + defen_text + '\n'
                out += wor

                card += 1
            except Exception as a:
                logger.warning(exc_info=a)
                if not self.notfound:
                    self.ui.textEdit.insertPlainText(u" не найдено:\n")
                    self.notfound = 1
                self.ui.textEdit.moveCursor(QTextCursor.End)
                try:
                    self.ui.textEdit.insertPlainText(u" %s   \n" % (i[:-1]))
                except:
                    self.ui.textEdit.insertPlainText('Codec error')
        tooltip(u'Генерированно: %d карт из %d ' % (card, c))
        return out

    def import_to(self):
        self.cart.close()
        if self.fileName_output and self.cards != '':
            self.model = self.ui.comboBox_3.currentText()
            logger.debug("model : " + self.model)
            noteModel = mw.col.models.byName(self.model)
            mw.col.models.setCurrent(noteModel)
            desc = self.ui.comboBox_2.currentText()
            noteModel['did'] = mw.col.decks.id(desc)
            importer = TextImporter(mw.col, self.fileName_output)
            importer.allowHTML = True
            importer.initMapping()
            importer.run()
            mw.deckBrowser.refresh()
            log = "\n".join(importer.log)
            if "\n" not in log:
                tooltip(log)
            else:
                showText(log)
        else:
            tooltip("I do not have cards to import".upper())

    def combo_chosen_action(self):
        text = self.ui.comboBox_4.currentText()
        if text == u'Импортировать':
            self.action_default = True
        elif text == u'Открыть без имп.':
            self.action_default = False

    def combo_chosen(self):
        text = self.ui.comboBox.currentText()
        if text == u'Румынский':
            self.lang_default = False
        elif text == u'Английский':
            self.lang_default = True

    def opener(self, path, mode):
        logger.debug('open'+ path)
        if mode == 'w':
            file = codecs.open(str(path), 'w', encoding='utf-8')
        else:
            file = codecs.open(str(path), 'r', encoding='utf-8')
        return file

    def begin(self, leng):
        self.words = []
        try:
            logger.debug('opening kindle file : '+ self.filename_kindle)
            clippingsfile = self.opener(self.filename_kindle, 'r')
        except Exception as e:
            logger.warning(e)
            self.filename_kindle = None
            clippingsfile = None
        if self.filename_kindle:
            kindle_notes = clippingsfile.readlines()
            clippingsfile.close()
            words_kindle = self.streap(kindle_notes)
            if words_kindle != []:
                self.words += words_kindle
        try:
            word_file = self.opener(self.filename_txt, 'r')
        except Exception as e:
            logger.warning(e)
            self.filename_txt = None
            word_file = None
        if self.filename_txt:
            words_txt = word_file.readlines()
            word_file.close()
            if words_txt != []:
                self.words += words_txt
        if self.one_word != u'':
            self.words.append(self.one_word)
        logger.debug("self.words is : {} \n and leng is {}".format(self.words, leng))
        if not self.words == [] and leng:
            logger.debug('gen en')
            self.cards = self.run
            logger.debug('len cards out is' + str(len(self.cards)))
            self.cart.write(self.cards)
            self.cart.close()
        elif not self.words == [] and not leng:
            logger.debug('gen ro' + '\n' + str(self.words))
            out = self.gen_ro(self.words)
            if not out == None:
                logger.debug('type out is' +  str(type(out)))
                self.cart.write(out)
            else:
                showInfo(u'Слова не найдены')
        else:
            logger.debug("Words don't found")
        #logger.debug("Action status:", self.action_default)
        if self.filename_kindle is None and self.filename_txt is None and self.words == []\
                or self.words == []:
            showInfo(u'Cлова не найдены')
        elif not self.action_default:
            cmd = '"C:\\Program Files\\Notepad++\\notepad++.exe"  "%s"' % self.fileName_output
            proc = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        else:
            self.import_to()
        self.cart.close()

    def main(self):
        self.combo_chosen()
        self.one_word = self.ui.lineEdit_4.text()
        try:
            if not self.lang_default:
                self.cart = self.opener(self.fileName_output, 'w')
            else:
                self.cart = codecs.open(self.fileName_output, mode='w', encoding="utf-8")
        except:
            self.cart = None

        if self.cart != None or self.one_word:
            self.begin(self.lang_default)

    def exec(self):
        self.window.show()
        self.window.exec_()

