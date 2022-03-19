import requests
import pandas as pd


def main():
    df = pd.DataFrame(data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    responses = df.apply(lambda row: requests.get(f"https://reqres.in/api/users/{row}").json(), axis = 1)
    print(responses)
    return


if __name__ == "__main__":
    main()
