#themoviedb
#note: right now, themoviedb only supports "en" for language
TMDB_GETINFO_IMDB = 'http://api.themoviedb.org/2.1/Movie.imdbLookup/en/json/a3dc111e66105f6387e99393813ae4d5/%s'
TMDB_GETINFO_TMDB = 'http://api.themoviedb.org/2.1/Movie.getInfo/en/json/a3dc111e66105f6387e99393813ae4d5/%s'
TMDB_GETINFO_HASH = 'http://api.themoviedb.org/2.1/Hash.getInfo/en/json/a3dc111e66105f6387e99393813ae4d5/%s'

def Start():
  HTTP.CacheTime = CACHE_1DAY
  
@expose
def GetImdbIdFromHash(openSubtitlesHash, lang):
  try:
    tmdb_dict = JSON.ObjectFromURL(TMDB_GETINFO_HASH % str(openSubtitlesHash))[0]
    if isinstance(tmdb_dict, dict) and tmdb_dict.has_key('imdb_id'):
      return MetadataSearchResult(
        id    = tmdb_dict['imdb_id'],
        name  = tmdb_dict['name'],
        year  = None,
        lang  = lang,
        score = 94)
    else:
      return None
    
  except:
    return None
  
class TMDbAgent(Agent.Movies):
  name = 'themoviedb'
  languages = [Locale.Language.English]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']
  
  def search(self, results, media, lang):
    if media.primary_metadata is not None:
      tmdb_id = self.get_tmdb_id(media.primary_metadata.id) # get the TMDb ID using the IMDB ID
      if tmdb_id:
        results.Append(MetadataSearchResult(id = tmdb_id, score = 100))
    elif media.openSubtitlesHash is not None:
      match = GetImdbIdFromHash(media.openSubtitlesHash, lang)

  def update(self, metadata, media, lang): 
    proxy = Proxy.Preview
    try:
      tmdb_dict = JSON.ObjectFromURL(TMDB_GETINFO_TMDB % metadata.id)[0] #get the full TMDB info record using the TMDB id
    except:
      Log('Exception fetching JSON from theMovieDB (1).')
      return None

    # Rating.
    votes = tmdb_dict['votes']
    rating = tmdb_dict['rating']
    if votes > 20:
      metadata.rating = rating
    
    # Tagline.
    metadata.tagline = tmdb_dict['tagline']
      
    # Content rating.
    metadata.content_rating = tmdb_dict['certification']
      
    # Summary.
    metadata.summary = tmdb_dict['overview']
    
    # Release date.
    try: metadata.originally_available_at = Datetime.ParseDate(tmdb_dict['released']).date()
    except: pass
      
    # Runtime.
    try: metadata.duration = int(tmdb_dict['runtime']) * 60 * 1000
    except: pass
      
    # Genres.
    metadata.genres.clear()
    for genre in tmdb_dict['genres']:
      metadata.genres.add(genre['name'])
      
    # Studio.
    try: metadata.studio = tmdb_dict['studios'][0]['name']
    except: pass

    # Cast.
    metadata.directors.clear()
    metadata.writers.clear()
    metadata.roles.clear()
    
    for member in tmdb_dict['cast']:
      if member['job'] == 'Director':
        metadata.directors.add(member['name'])
      elif member['job'] == 'Author':
        metadata.writers.add(member['name'])
      elif member['job'] == 'Actor':
        role = metadata.roles.new()
        role.role = member['character']
        role.actor = member['name']
    
    i = 0
    for p in tmdb_dict['posters']:
      if p['image']['size'] == 'original':
        if p['image']['url'] not in metadata.posters:
          p_id = p['image']['id']
          for t in tmdb_dict['posters']:
            if t['image']['id'] == p_id and t['image']['size'] == 'mid':
              thumb = HTTP.Request(t['image']['url'])
              i += 1
              break
          try: metadata.posters[p['image']['url']] = proxy(thumb, sort_order = i)
          except: pass
    
    i = 0
    for b in tmdb_dict['backdrops']:
      if b['image']['size'] == 'original':     
        if b['image']['url'] not in metadata.art:
          b_id = b['image']['id']
          for t in tmdb_dict['backdrops']:
            if t['image']['id'] == b_id and t['image']['size'] == 'poster':
              thumb = HTTP.Request(t['image']['url'])
              i += 1
              break 
          try: metadata.art[b['image']['url']] = proxy(thumb, sort_order = i)
          except: pass
    
  def get_tmdb_id(self, imdb_id):
    try:
      tmdb_dict = JSON.ObjectFromURL(TMDB_GETINFO_IMDB % str(imdb_id))[0]
    except:
      Log('Exception fetching JSON from theMovieDB (2).')
      return None
    if tmdb_dict and isinstance(tmdb_dict, dict):
      return str(tmdb_dict['id'])
    else:
      return None
