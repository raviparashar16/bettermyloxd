import argparse
from scrape import LetterboxdScraper

def main():
    parser = argparse.ArgumentParser(description='Get random movie recommendation from Letterboxd watchlist(s)')
    parser.add_argument('-u', '--usernames', nargs='+', type=str, required=True, 
                       help='valid public Letterboxd profile usernames (min 1, max 5)', metavar='USERNAME')
    parser.add_argument('-e', '--exclude', nargs='+', type=str, default=[],
                       help='Movie IDs to exclude (max 5)', metavar='MOVIE_ID')
    args = parser.parse_args()

    if len(args.usernames) > 5:
        parser.error("Maximum 5 usernames allowed")
    if len(args.exclude) > 5:
        parser.error("Maximum 5 excluded movies allowed")

    scraper = LetterboxdScraper()
    movie = scraper.scrape(args.usernames, args.exclude)

    if movie:
        print(f"Movie ID: {movie.movie_id}")
        print(f"Letterboxd URL: {movie.letterboxd_url}")
    else:
        print("No movies found matching criteria")

if __name__ == "__main__":
    main()
