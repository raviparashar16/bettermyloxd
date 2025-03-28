import argparse
from scrape import LetterboxdScraper

def main():
    parser = argparse.ArgumentParser(description='Get random movie recommendation from Letterboxd watchlist(s)')
    parser.add_argument('-u', '--usernames', nargs='+', type=str, required=True, 
                       help='valid public Letterboxd profile usernames (min 1, max 5)', metavar='USERNAME')
    parser.add_argument('-n', '--num_movies', type=int, default=1,
                       help='Number of movies to return (default 1, max 5)', metavar='NUM_MOVIES')
    parser.add_argument('-e', '--exclude', nargs='+', type=str, default=[],
                       help='Movie IDs to exclude (max 5)', metavar='MOVIE_ID')
    args = parser.parse_args()

    if args.num_movies > 5:
        parser.error("Maximum 5 movies allowed")
    if len(args.usernames) > 5:
        parser.error("Maximum 5 usernames allowed")
    if len(args.exclude) > 5:
        parser.error("Maximum 5 excluded movies allowed")

    scraper = LetterboxdScraper()
    movie_list = scraper.scrape(args.num_movies, args.usernames, args.exclude)

    if movie_list:
        for movie_num, movie in enumerate(movie_list):
            print(f"Movie {movie_num + 1}--------------------------------")
            print(f"Title: {movie.title}")
            print(f"Movie ID: {movie.movie_id}")
            print(f"Letterboxd URL: {scraper.site_url}{movie.letterboxd_path}")
            print(f"Image URL: {scraper.film_url_start}{movie.letterboxd_path}{scraper.film_url_end}")
    else:
        print("No movies found matching criteria")

if __name__ == "__main__":
    main()
