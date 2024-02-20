import requests
from bs4 import BeautifulSoup
import re
from lxml import html
import pandas as pd
import pickle
import os
from tqdm import tqdm


def generate_movies_database_urls_list(base_url):
    movies_database_urls = []
    for i in range(1, 34):
        url_prefix = '&page=' + str(i)
        movies_database_urls.append(base_url+url_prefix)
    return movies_database_urls

def generate_movies_urls_list(linkblu_divs):
    urls_list = []
    for linkblu_div in linkblu_divs:
        h2_tag = linkblu_div.find("h2")
        if h2_tag:
            link_a_tag = h2_tag.find("a")
            if link_a_tag:
                url = link_a_tag.get("href")
                urls_list.append(url)
    return urls_list

def generate_all_movies_urls_list(search_url):
    movies_database_urls_list = generate_movies_database_urls_list(search_url)
    all_movies_urls_list = []
    for count, current_movies_page_url in enumerate(tqdm(movies_database_urls_list, desc="Retrieving pages urls")):
        page = requests.get(current_movies_page_url)
        if page.status_code == 200:
            soup = BeautifulSoup(page.content, 'html.parser')
            all_movies_urls_list.append(generate_movies_urls_list(soup.find_all("div", class_="linkblu")))
    all_movies_urls_list = [url for sublist in all_movies_urls_list for url in sublist]
    print('Done.')
    return all_movies_urls_list

def load_or_create_pickle(file_path, search_filtered_url):
    try:
        with open(file_path, 'rb') as pickle_file:
            loaded_list = pickle.load(pickle_file)
        print('Urls list loaded.')
        return loaded_list
    except FileNotFoundError:
        print(f"The pickle file '{file_path}' does not exist.")
        print('Proceeding with the creation of the urls:')
        new_list = generate_all_movies_urls_list(search_filtered_url)
        with open(file_path, 'wb') as pickle_file:
            pickle.dump(new_list, pickle_file)
        return new_list
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_MyMovies_dataset(save_path, movies_urls):
    movies_df = pd.DataFrame(columns=['MovieName', 'Director', 'Cast', 'Duration', 'ReleaseDate', 'Genre', 'Production',
                                      'Rating_MyMovies', 'Rating_Critic', 'Rating_Public', 'Rating_Average',
                                      'TopParagraph', 'BottomParagraph'])

    for movie_url in tqdm(movies_urls, desc="Processing movies", unit="movie"):
        # Initialize variables
        movie_info = {
            'MovieName': '',
            'Director': '',
            'Cast': '',
            'Duration': '',
            'ReleaseDate': '',
            'Genre': '',
            'Production': '',
            'Rating_MyMovies': '',
            'Rating_Critic': '',
            'Rating_Public': '',
            'Rating_Average': '',
            'TopParagraph': '',
            'BottomParagraph': ''
        }

        # Fetch the page
        page = requests.get(movie_url)
        if page.status_code != 200:
            print(f"Failed to fetch the page. Status code: {page.status_code}")
            continue

        soup = BeautifulSoup(page.content, 'html.parser')

        titolo_div = soup.find("div", class_="titolo")
        if titolo_div:
            h1_element = titolo_div.find("h1")
            if h1_element:
                movie_info['MovieName'] = h1_element.text.strip()
                # print(movie_info['MovieName'])

        highlights_p = soup.find("p", class_="highlights")
        if highlights_p:
            highlights_p_text = highlights_p.get_text().strip()
            # print(highlights_p_text)
            movie_info['BottomParagraph'] = highlights_p_text

        sottotitolo_rec_p = soup.find("p", class_="sottotitolo_rec")
        if sottotitolo_rec_p:
            sottotitolo_rec_p_text = re.sub(r'\s+', ' ', sottotitolo_rec_p.get_text().strip())
            # print(sottotitolo_rec_p_text)
            movie_info['TopParagraph'] = sottotitolo_rec_p_text

            director_match = re.search(r'Regia di (.*?)[.]', sottotitolo_rec_p_text)
            if director_match:
                movie_info['Director'] = director_match.group(1).strip()
                # print(f"Director: {movie_info['Director']}")

            cast_match = re.search(r'con (.+?)\.', sottotitolo_rec_p_text)
            if cast_match:
                movie_info['Cast'] = cast_match.group(1).strip()
                # print(f"Cast: {movie_info['Cast']}")

            duration_match = re.search(r'durata (\d+) minuti', sottotitolo_rec_p_text)
            if duration_match:
                movie_info['Duration'] = duration_match.group(1).strip()
                # print(f"Duration: {movie_info['Duration']}")

            release_date_match = re.search(r'Uscita cinema \w+ (\d+ \w+ \d{4})', sottotitolo_rec_p_text)
            if release_date_match:
                movie_info['ReleaseDate'] = release_date_match.group(1).strip()
                # print(f"Release date: {movie_info['ReleaseDate']}")

            production_match = re.search(r'distribuito da (.+?)\.', sottotitolo_rec_p_text)
            if production_match:
                movie_info['Production'] = production_match.group(1).strip()
                # print(f"Production: {movie_info['Production']}")

            genre_match = re.search(r'Genere (.+?),', sottotitolo_rec_p_text)
            if genre_match:
                movie_info['Genre'] = genre_match.group(1).strip()
                # print(f"Genre: {movie_info['Genre']}")
        # else:
        #     print("No 'sottotitolo_rec' p found on the page.")

        mm_tiny_divs = soup.find_all("div", class_="mm-tiny")
        for mm_tiny_div in mm_tiny_divs:
            mm_tiny_text = mm_tiny_div.get_text().strip()

            my_movies_rating_match = re.search(r'(MYMOVIES) (\d+,\d+)', mm_tiny_text)
            if my_movies_rating_match:
                movie_info['Rating_MyMovies'] = my_movies_rating_match.group(2)
                # print(f"MyMovies rating: {movie_info['Rating_MyMovies']}")

            critic_rating_match = re.search(r'(CRITICA) (\d+,\d+)', mm_tiny_text)
            if critic_rating_match:
                movie_info['Rating_Critic'] = critic_rating_match.group(2)
                # print(f"Critic rating: {movie_info['Rating_Critic']}")

            public_rating_match = re.search(r'(PUBBLICO) (\d+,\d+)', mm_tiny_text)
            if public_rating_match:
                movie_info['Rating_Public'] = public_rating_match.group(2)
                # print(f"Public rating: {movie_info['Rating_Public']}")

        rating_span = soup.find("span", class_="rating")
        if rating_span:
            movie_info['Rating_Average'] = rating_span.text.strip()
            # print(f'Average rating: {movie_info['Rating_Average']}')

        new_row = pd.DataFrame(movie_info, index=[0])
        movies_df = pd.concat([movies_df, new_row], ignore_index=True)

    movies_df.to_csv(save_path, index=False)

def main():
    year = 2022
    nationality = 'Italia'
    main_search_url = 'https://www.mymovies.it/database/ricerca/avanzata/?titolo=&titolo_orig=&regista=&attore=&id_genere=-1&nazione=' \
                      + nationality + '&clausola1=%3D&anno_prod=' + str(year) \
                      + '&clausola2=-1&stelle=-1&id_manif=-1&anno_manif=&disponib=-1&ordinamento=0&submit=Inizia+ricerca+%C2%BB'

    base_path = os.path.join(os.getcwd(), 'data')
    pkl_save_path = os.path.join(base_path, f'all_movies_urls{year}.pkl')
    movies_urls_list = load_or_create_pickle(pkl_save_path, main_search_url)
    dataset_save_path = os.path.join(base_path, f'movies_data{year}.csv')
    if not os.path.exists(dataset_save_path):
        print('Generating dataset:')
        generate_MyMovies_dataset(dataset_save_path, movies_urls_list)
        print(f"Dataset generated and saved at: {dataset_save_path}")
    else:
        print(f"Dataset already exists at: {dataset_save_path}")


main()

# movies_dataset_df = pd.read_csv(dataset_save_path)
# print(movies_dataset_df)
