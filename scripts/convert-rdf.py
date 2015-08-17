
import rdflib
import argparse


def print_usage():
    print("usage: " + sys.argv[0] + " <in_format> <out_format> <file>")


def load(graph, file, format="turtle"):
	graph.load(file, format=format)


def serialize(graph, format="xml"):
    if format == "json-ld":
        return graph.serialize(format='json-ld', indent=2).decode()
    elif format == "nt":
        return graph.serialize(format='nt').decode()
    else:
        return graph.serialize(format=format, encoding="UTF-8").decode(encoding="UTF-8")


def main(file, in_format, out_format):
	g = rdflib.Graph()
	load(g, file=file, format=in_format)
	print(serialize(g, format=out_format))


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('--format', metavar='FMT_IN', default='turtle', help='input format')
	parser.add_argument('--out', metavar='FMT_OUT', default='turtle', help='output format')
	parser.add_argument('file', metavar='FILE', help='RDF file to load')

	args = parser.parse_args()
	main(file=args.file, in_format=args.format, out_format=args.out)
