from argparse import ArgumentParser, Namespace

parser = ArgumentParser()
parser.add_argument('--port', type=int, required=True)
parser.add_argument('--service-token', required=True)

args: Namespace = parser.parse_args()


port: int = args.port
service_token: str = args.service_token
max_bots_limit: int = 50
