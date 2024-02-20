### MyMovies.it scraper

This Python script scrapes movie data from [MYmovies.it](https://www.mymovies.it/) using `BeautifulSoup`, generating a dataset of movies. Currently, I've filtered the movies by nationality=Italian and year.

The dataset generated is saved in CSV format for further analysis, containing information such as movie name, director, cast, duration, release date, genre, production, ratings, summaries, etc.

### Usage:
1. Set the `year` and `nationality` variables in the `main()` function to specify the year and nationality of the movies to scrape. Adding additional filters is pretty straightforward.
2. Run the script to generate the dataset.
3. Access the generated CSV file containing movie data for analysis.
