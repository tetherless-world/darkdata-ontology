
import rdflib
import argparse


def main(file, in_format, out_format):
	g = rdflib.Graph()
	g.load(file, format=in_format)

	if out_format == "json-ld":
        return g.serialize(format='json-ld', indent=2).decode()
    elif out_format == "nt":
        return g.serialize(format='nt').decode()
    else:
        return g.serialize(format=out_format, encoding="UTF-8").decode(encoding="UTF-8")


if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument('--format', metavar='FMT_IN', default='turtle', help='input format')
	parser.add_argument('--out', metavar='FMT_OUT', default='turtle', help='output format')
	parser.add_argument('file', metavar='FILE', help='RDF file to load')

	args = parser.parse_args()
	main(file=args.file, in_format=args.format, out_format=args.out)
