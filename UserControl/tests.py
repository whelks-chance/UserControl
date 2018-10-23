import requests


class Tests:
    def create_user(self):
        response = requests.get('http://localhost:8000/generate_new_user')
        print(response)

        res_json = response.json()
        print(res_json)

        if len(res_json['errors']):
            print('has errors')

    def check_users(self):
        response = requests.get('http://localhost:8000/check_users')
        print(response)

        res_json = response.json()
        print(res_json)

        if len(res_json['errors']):
            print('has errors')


if __name__ == '__main__':
    t = Tests()

    # t.create_user()
    t.check_users()
