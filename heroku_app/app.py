from flask import Flask, render_template, request, redirect, url_for, session
import numpy as np
import pandas as pd
import requests
import matplotlib.pyplot as plt
import secrets
import random

secret = secrets.token_urlsafe(32)
header = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'}


api_key = ""

app = Flask(__name__, template_folder='templates')

app.secret_key = secret

def find_song(artist, track):
    results = []
    artists_list = []
    params_get_artists = {
        "method" : "artist.search",
        "format" : "json",
        "limit" : 250,
        "artist" : artist,
        "api_key" : api_key
    }
    artists = requests.get('https://ws.audioscrobbler.com/2.0/', params=params_get_artists, headers = header)
    for artist in artists.json()['results']['artistmatches']['artist']:
        artists_list.append(artist['name'])

    tracks_list = []
    params_get_tracks = {
        "method" : "track.search",
        "format" : "json",
        "limit" : 250,
        "track" : track,
        "api_key" : api_key
    }
    tracks = requests.get('https://ws.audioscrobbler.com/2.0/', params=params_get_tracks, headers = header)

    for track in tracks.json()['results']['trackmatches']['track']:
        if track['artist'] in artists_list:
            return_track = track['name']
            return_artist = track['artist']
            results.append((return_artist, return_track))

    return results





def get_artist_info(result_artist):
    params_artist_info = {
    "method" : "artist.getInfo",
    "format" : "json",
    "artist" : result_artist,
    "api_key" : api_key
}
    artist_info = requests.get('https://ws.audioscrobbler.com/2.0/', params=params_artist_info, headers = header)
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
    track_info = requests.get('https://ws.audioscrobbler.com/2.0/', params=params_track_info, headers = header)
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
    similar_tracks = requests.get('https://ws.audioscrobbler.com/2.0/', params=params_get_similar_tracks, headers = header)
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
    artist_info = requests.get('https://ws.audioscrobbler.com/2.0/', params=params_artist_counts, headers = header)
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
    similar_artists = requests.get('https://ws.audioscrobbler.com/2.0/', params=params_get_similar_artists, headers = header)
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
        session['artist'] = request.form['artist']
        session['track'] = request.form['track']
        return redirect(url_for("result"))

@app.route('/result', methods = ['GET', 'POST'])
def result():
    if request.method == 'POST':
        return redirect(url_for("main"))

    if request.method == 'GET':
        artist = session.get('artist', None)
        track = session.get('track', None)


        results = find_song(artist = artist, track = track)
        if len(results) > 0:
            result_artist = results[0][0]
            result_track = results[0][1]
        else:
            return redirect(url_for("not_found"))

        listeners, playcount, artist_info = get_artist_info(result_artist)

        track_duration, track_listeners, track_playcounts, track_album, track_content = get_track_info(result_artist, result_track)

        sim_tracks_df = get_similar_tracks(result_artist, result_track)

        fig, ax = plt.subplots(figsize=(16, 9))
        ax1 = ax.bar(sim_tracks_df['Info'], sim_tracks_df['Playcount'], label = 'Playcount', color = 'black')
        ax2 = ax.bar(sim_tracks_df['Info'], sim_tracks_df['Listeners'], label = 'Listeners', color = 'white')
        ax.ticklabel_format(style='plain', axis='y')
        ax.set_facecolor((.5, .5, .5))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=70)
        plt.yticks(color = 'white', fontsize = 15)
        plt.xticks(color = 'white', fontsize = 15)
        plt.legend()
        fig.savefig('static/sim_tracks.png', facecolor = (.1, .1, .1), bbox_inches = "tight")

        sim_art_df = get_similar_artists(result_artist)

        fig, ax = plt.subplots(figsize=(16, 9))
        ax1 = ax.bar(sim_art_df['Info'], sim_art_df['Playcount'], label = 'Playcount', color = 'black')
        ax2 = ax.bar(sim_art_df['Info'], sim_art_df['Listeners'], label = 'Listeners', color = 'white')
        ax.ticklabel_format(style='plain', axis='y')
        ax.set_facecolor((.5, .5, .5))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=70)
        plt.yticks(color = 'white', fontsize = 15)
        plt.xticks(color = 'white', fontsize = 15)
        plt.legend()
        fig.savefig('static/sim_artists.png', facecolor = (.1, .1, .1), bbox_inches = "tight")

        image1_url = 'static/sim_tracks.png' + '?' + str(random.randint(1, 10000))
        image2_url = 'static/sim_artists.png' + '?' + str(random.randint(1, 10000))

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
