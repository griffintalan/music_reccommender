from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np
import pandas as pd
import requests
import time
import matplotlib.pyplot as plt
import secrets
import random

secret = secrets.token_urlsafe(32)

api_key = "6bb7f55c691d1bdff841fdc67934b3b8"

app = Flask(__name__, template_folder='templates')

app.secret_key = secret

def find_song(artist, track):
    results = []
    artists_list = []
    params_get_artists = {
        "method" : "artist.search",
        "format" : "json",
        "limit" : 100,
        "artist" : artist,
        "api_key" : api_key
    }
    artists = requests.get('http://ws.audioscrobbler.com/2.0/', params=params_get_artists)
    for artist in artists.json()['results']['artistmatches']['artist']:
            artists_list.append(artist['name'])

    tracks_list = []
    params_get_tracks = {
        "method" : "track.search",
        "format" : "json",
        "limit" : 100,
        "track" : track,
        "api_key" : api_key
    }
    tracks = requests.get('http://ws.audioscrobbler.com/2.0/', params=params_get_tracks)
    for track in tracks.json()['results']['trackmatches']['track']:
        if track['artist'] in artists_list:
            return_track = track['name']
            return_artist = track['artist']
            results.append((return_artist, return_track))
    if len(results) > 0:
        return results
    return('Could not find track. Please search again.')



def get_artist_info(result_artist):
    params_artist_info = {
    "method" : "artist.getInfo",
    "format" : "json",
    "artist" : result_artist,
    "api_key" : api_key
}
    artist_info = requests.get('http://ws.audioscrobbler.com/2.0/', params=params_artist_info)
    try:
        content = artist_info.json()['artist']['bio']['content']
    except:
        content = 'No artist information found.'
    listeners = int(artist_info.json()['artist']['stats']['listeners'])
    playcount = int(artist_info.json()['artist']['stats']['playcount'])
    return (listeners, playcount, content)

def get_track_info(result_artist, result_track):
    params_track_info = {
    "method" : "track.getInfo",
    "format" : "json",
    "artist" : result_artist,
    "track" : result_track,
    "api_key" : api_key
}
    track_info = requests.get('http://ws.audioscrobbler.com/2.0/', params=params_track_info)
    track_listeners = int(track_info.json()['track']['listeners'])
    track_playcounts = int(track_info.json()['track']['playcount'])
    track_duration = int(track_info.json()['track']['duration'])
    try:
        track_content = track_info.json()['track']['wiki']['content']
    except:
        track_content = 'Track information unavailable.'
    try:
        track_album = track_info.json()['track']['album']['title']
    except:
        track_album = 'Album unavailable.'
    return (track_duration, track_listeners, track_playcounts, track_album, track_content)


def get_similar_tracks(result_artist, result_track):
    params_get_similar_tracks = {
        "method" : "track.getSimilar",
        "format" : "json",
        "artist" : result_artist,
        "track" : result_track,
        "api_key" : api_key
    }
    df = pd.DataFrame(columns = ['Info', 'Album', 'Duration', 'Listeners', 'Playcount'])
    similar_tracks = requests.get('http://ws.audioscrobbler.com/2.0/', params=params_get_similar_tracks)
    counter = 1
    for sim_track in similar_tracks.json()['similartracks']['track'][:10]:
        return_similar_track = sim_track['name']
        return_similar_artist = sim_track['artist']['name']
        sim_track_duration, sim_track_listeners, sim_track_playcounts, sim_track_album, sim_track_content = get_track_info(return_similar_artist, return_similar_track)
        sim_df = pd.DataFrame({'Info' : [str(counter) + '. ' + return_similar_track + ' \n ' + return_similar_artist],
                               'Album' : [sim_track_album],
                               'Duration' : [sim_track_duration],
                               'Listeners' : [sim_track_listeners],
                               'Playcount' : [sim_track_playcounts]})
        df = df.append(sim_df, ignore_index= True)
        counter += 1
    return df


def get_artist_counts(result_artist):
    params_artist_counts = {
    "method" : "artist.getInfo",
    "format" : "json",
    "artist" : result_artist,
    "api_key" : api_key
}
    artist_info = requests.get('http://ws.audioscrobbler.com/2.0/', params=params_artist_counts)
    listeners = int(artist_info.json()['artist']['stats']['listeners'])
    playcount = int(artist_info.json()['artist']['stats']['playcount'])
    return (listeners, playcount)

def get_similar_artists(result_artist):
    params_get_similar_artists = {
        "method" : "artist.getSimilar",
        "format" : "json",
        "artist" : result_artist,
        "api_key" : api_key
    }
    similar_artists = requests.get('http://ws.audioscrobbler.com/2.0/', params=params_get_similar_artists)
    df_sim_artists = pd.DataFrame(columns = ['Info', 'Listeners', 'Playcount'])
    counter = 1
    for artist in similar_artists.json()['similarartists']['artist'][:10]:
        return_similar_artist_art = artist['name']
        sim_art_listeners, sim_art_playcount = get_artist_counts(return_similar_artist_art)
        df_sim_artists_art = pd.DataFrame({'Info' : [str(counter) + '. ' + return_similar_artist_art],
                                         'Listeners' : [sim_art_listeners],
                                         'Playcount' : [sim_art_playcount]})
        df_sim_artists = df_sim_artists.append(df_sim_artists_art, ignore_index = True)
        counter += 1
    return df_sim_artists


@app.route('/', methods = ['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template('main.html')
    if request.method == 'POST':
        session['artist'] = request.form['artist']
        session['track'] = request.form['track']
        return redirect(url_for("result"))

@app.route('/not_found', methods = ['GET', 'POST'])
def not_found():
    if request.method == 'GET':
        return render_template('not_found.html')
    if request.method == 'POST':
        return redirect(url_for("main"))

@app.route('/result', methods = ['GET', 'POST'])
def result():
    if request.method == 'POST':
        return redirect(url_for("main"))

    if request.method == 'GET':
        artist = session.get('artist', None)
        track = session.get('track', None)

        try:
            results = find_song(artist = artist, track = track)
            result_artist = results[0][0]
            result_track = results[0][1]
        except:
            return redirect(url_for("not_found"))

        listeners, playcount, artist_info = get_artist_info(result_artist)

        track_duration, track_listeners, track_playcounts, track_album, track_content = get_track_info(result_artist, result_track)

        sim_tracks_df = get_similar_tracks(result_artist, result_track)

        plt.figure(figsize = (16, 9))
        plt.plot(sim_tracks_df['Info'], sim_tracks_df['Duration'], label = 'Duration')
        plt.plot(sim_tracks_df['Info'], sim_tracks_df['Listeners'], label = 'Listeners')
        plt.plot(sim_tracks_df['Info'], sim_tracks_df['Playcount'], label = 'Playcount')
        plt.xticks(rotation = 45)
        plt.ticklabel_format(style='plain', axis='y')
        plt.ylabel('Count')
        plt.legend()
        plt.tight_layout()
        plt.savefig('static/test.png')

        sim_art_df = get_similar_artists(result_artist)

        plt.figure(figsize = (16, 9))
        plt.plot(sim_art_df['Info'], sim_art_df['Listeners'], label = 'Listeners')
        plt.plot(sim_art_df['Info'], sim_art_df['Playcount'], label = 'Playcount')
        plt.xticks(rotation = 60)
        plt.ticklabel_format(style='plain', axis='y')
        plt.legend()
        plt.tight_layout()
        plt.savefig('static/test2.png')

        image1_url = 'static/test.png' + '?' + str(random.randint(1, 10000))
        image2_url = 'static/test2.png' + '?' + str(random.randint(1, 10000))

        return render_template('result.html',
                                     result_artist = result_artist,
                                     result_track = result_track,
                                     listeners = listeners,
                                     playcount = playcount,
                                     artist_info = artist_info,
                                     track_duration = track_duration,
                                     track_listeners = track_listeners,
                                     track_playcounts = track_playcounts,
                                     track_album = track_album,
                                     track_content = track_content,
                                     image1_url = image1_url,
                                     image2_url = image2_url)




if __name__ == '__main__':
    app.run()
