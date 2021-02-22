#
# Модуль, который отвечает за парсинг
# отдельной страницы аниме с world-art
#
import re

from anime import Anime





# functions
def parse_anime(soup) -> Anime:
	'''
	Данная функция производит парсинг страницы
	аниме с сайта world-art; на вход принимается
	объекта типа BeautifulSoup, установленный
	на корень страницы, на выходе выдаётся
	заполненный объект Anime;
	'''

	# object to fill
	anime = Anime(
		name = '',
		fields = {
			'engname'  : { 'hint' : 'Название',          'tr' : null         },
			'country'  : { 'hint' : 'Производство',      'tr' : null         },
			'genre'    : { 'hint' : 'Жанр',              'tr' : genre_parse  },
			'target'   : { 'hint' : 'Целевая аудитория', 'tr' : null         },
			'type'     : { 'hint' : 'Тип',               'tr' : type_parse   },
			'base'     : { 'hint' : 'Основа',            'tr' : null         },
			'season'   : { 'hint' : 'Сезон',             'tr' : season_parse },
			'director' : { 'hint' : 'Режиссёр',          'tr' : null         },
			'score'    : { 'hint' : 'Средний балл',      'tr' : score_parse  },
			'voted'    : { 'hint' : 'Проголосовало',     'tr' : voted_parse  },
			'rating'   : { 'hint' : 'Место в рейтинге',  'tr' : rating_parse },
		},
		tags = {
			#  'tagname' : {
				#  'desc' : 'description...', 
				#  'score' : int
			#  }
		},
		annotation = None,
		coms = []
	)



	# get name
	namesoup = soup.find(
		lambda tag:
			tag.name == 'font' and
			tag.has_attr('size') and
			tag['size'] == '5'
	)

	if namesoup is None:
		return None

	anime.name = namesoup.text

	# fields
	table = (
		soup.body.center.find_all('table')[6].
		tr.td.table.tr.contents[4].
		find_all('table')[1].
		find_all('tr')[1].contents[2]
	)

	for f in anime.fields:
		tag = table.find(lambda tag:
			re.match(anime.fields[f]['hint'], tag.text) is not None and
			tag.b is not None and 
			tag.b.text.startswith(anime.fields[f]['hint'])
		)
		if tag is None:
			anime.fields[f] = None
		else:
			anime.fields[f] = anime.fields[f]['tr'](tag.find_all('td')[2].text.strip())

	if anime.fields['season'] is None:
		tag = table.find(lambda tag: re.match('Выпуск', tag.text) is not None)
		if tag is not None:
			anime.fields['season'] = release_parse(tag.find_all('td')[2].text.strip())

	# tags
	for tag in soup.select('.newtag'):
		anime.tags[tag.a.text] = {
			'desc' : tag.a['title'],
			'score' : float(tag.font.text)
		}

	# annotation
	try:
		anime.annotation = (
			soup.center.find_all('table')[6].
			tr.td.table.tr.contents[4].
			contents[14].tr.td.p.text
		)
	except:
		pass

	# comments
	try:
		bestcoms = soup.find( lambda tag: tag.text.strip() == 'Лучшие отзывы на это аниме' )
		t = nsib(bestcoms, 5)
		anime.coms.append( com_parse(t.p) )
		t = nsib(t, 6)
		anime.coms.append( com_parse(t.p) )
		t = nsib(t, 6)
		anime.coms.append( com_parse(t.p) )
	except:
		pass

	return anime



def print_anime(anime : Anime, style='short'):
	'''
	Печатает данные аниме на экран; переменная
	style может принимать следующие значения:
	  - 'short'  — Только нозвание поля и теги
	  - 'medium' — Ещё и краткий обзор (annotation)
	  - 'full'   — + три лучших обзора
	'''
	print(anime.name)
	print()

	for f in anime.fields.items():
		print(f[0] + ' ' * (11 - len(f[0])), f[1])
	print()

	for tag in anime.tags:
		print(tag + ' ' * (25 - len(tag)), anime.tags[tag]['score'])

	if style == 'short':
		return

	print('\n\nКраткий обзор\n')
	print(anime.annotation)

	if style == 'medium':
		return

	print('\n\nЛучшие обзоры\n')
	for com in anime.coms:
		print(com, end='\n'*5)
	return





# help parse functions
def nsib(tag, c):
	for i in range(c):
		tag = tag.next_sibling
	return tag

def null(a):
	return a

def genre_parse(genres : str) -> list:
	return genres.split(', ')

def type_parse(atype : str) -> dict:
	res = {
		'type' : 'tv'   if atype.startswith('ТВ') else
				 'ova'  if atype.startswith('OVA') else
				 'film' if atype.startswith('полнометражный фильм') else
				 'unknown',
	}

	if res['type'] == 'tv' or res['type'] == 'ova':
		s = re.search(r'\([^\d]*(\d+).*\)', atype)
		if s is None:
			res['epsc'] = 1
		else:
			res['epsc'] = int(s.group(1))
	elif res['type'] == 'film':
		res['epsc'] = 1
	else:
		res['epsc'] = None
	
	s = re.search(r',[^\d]*(\d+)', atype)
	if s is None:
		res['duration'] = None
	else:
		res['duration'] = int(s.group(1))
	return res

def season_parse(season : str) -> dict:
	return {
		'year' : int(season[-4:]),
		'season' : {
			'зима'  : 0,
			'весна' : 1,
			'лето'  : 2,
			'осень' : 3
		}[season[:season.find('-')]]
	}

def release_parse(release : str) -> dict:
	match = re.search(r'\d\d\.(\d\d)\.(\d\d\d\d)', release)
	if match is None:
		return { 'year' : None, 'season' : None }
	month = int(match.group(1))
	year  = int(match.group(2))
	return {
		'year'   : year,
		'season' : ['зима', 'весна', 'лето', 'осень'][month % 12 // 3]
	}

def score_parse(score : str) -> float:
	return float( re.match(r'\d+(\.\d+)?', score).group(0) )

def voted_parse(voted : str) -> int:
	return int(voted.split(' ')[0])

def rating_parse(rating : str) -> int:
	return int(rating.split(' ')[0])

def com_parse(com) -> str:
	res = ''
	for t in com.contents:
		if t.name is None:
			res += t.string
		elif t.name == 'br':
			res += '\n'
		else:
			raise Exception('unknown tag in com_parse')
	return res





# end
