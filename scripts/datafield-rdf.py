import xml.etree.ElementTree as etree
import csv
import rdflib
import urllib
import urllib.parse


def write_csv(data):
    with open('g3_datafields.csv', 'w') as csvfile:
        fieldnames = ['id',
                      "product gcmd id",
                      "sds name",
                      'product',
                      'product version',
                      'processing level',
                      'measurements',
                      'keywords',
                      'time interval',
                      'spatial resolution',
                      'instrument',
                      'platform',
                      'platform instrument']

        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def write_rdf(data):
    URI_BASE = "http://darkdata.tw.rpi.edu/data/"

    g = rdflib.Graph()
    DCT = rdflib.Namespace("http://purl.org/dc/terms/")
    DC = rdflib.Namespace("http://purl.org/dc/elements/1.1/")
    DD = rdflib.Namespace("http://www.purl.org/twc/ns/darkdata#")
    SSN = rdflib.Namespace("http://purl.oclc.org/NET/ssnx/ssn#")

    g.bind("dct", DCT)
    g.bind("dc", DC)
    g.bind("dd", DD)
    g.bind("ssn", SSN)

    for item in data:
        r = g.resource(rdflib.URIRef(URI_BASE + "datafield/" + item["id"]))
        r.add(rdflib.RDF.type, DD.DataField)
        r.add(DCT.identifier, rdflib.Literal(item["id"]))

        for _measurement in item["measurements"].split(";"):
            measurement = g.resource(rdflib.URIRef(URI_BASE + "measurement/" + urllib.parse.quote_plus(_measurement)))
            measurement.add(rdflib.RDF.type, DD.Measurement)
            measurement.add(rdflib.RDF.type, SSN.Property)
            measurement.add(rdflib.RDF.type, DD.ObservableProperty)

            measurement.add(rdflib.RDFS.label, rdflib.Literal(_measurement))
            r.add(DD.measurement, measurement)

        if "processing level" in item:
            _processing_level = item["processing level"]
            r.add(DD.processingLevel, rdflib.Literal(_processing_level, datatype=rdflib.XSD.integer))

        if "versioned product" in item:
            _product = item["product"]
            _product_version = item["product version"]
            _versioned_product = item["versioned product"]

            versioned_product = g.resource(rdflib.URIRef(URI_BASE + "versioned-product/" + urllib.parse.quote_plus(_versioned_product)))
            versioned_product.add(rdflib.RDF.type, DD.VersionedDataProduct)
            versioned_product.add(rdflib.RDFS.label, rdflib.Literal(_versioned_product))
            versioned_product.add(DD.version, rdflib.Literal(_product_version))

            product = g.resource(rdflib.URIRef(URI_BASE + "product/" + urllib.parse.quote_plus(_product)))
            product.add(rdflib.RDF.type, DD.DataProduct)
            product.add(rdflib.RDFS.label, rdflib.Literal(_product))

            versioned_product.add(DCT.isVersionOf, product)
            product.add(DCT.hasVersion, versioned_product)

            r.add(DCT.isPartOf, versioned_product)
            versioned_product.add(DCT.hasPart, r)

        if "time interval" in item:
            _time_interval = item["time interval"]
            time_interval = g.resource(
                rdflib.URIRef(URI_BASE + "time-interval/" + urllib.parse.quote_plus(_time_interval)))
            time_interval.add(rdflib.RDF.type, DD.TimeInterval)
            time_interval.add(rdflib.RDFS.label, rdflib.Literal(_time_interval))
            r.add(DD.timeInterval, time_interval)

        if "spatial resolution" in item:
            _spatial_resolution = item["spatial resolution"]
            spatial_resolution = g.resource(
                rdflib.URIRef(URI_BASE + "spatial-resolution/" + urllib.parse.quote_plus(_spatial_resolution)))
            spatial_resolution.add(rdflib.RDF.type, DD.SpatialResolution)
            spatial_resolution.add(rdflib.RDFS.label, rdflib.Literal(_spatial_resolution))
            r.add(DD.spatialResolution, spatial_resolution)

        if "platform" in item and item["platform"] is not None:
            _platform = item["platform"]
            platform = g.resource(rdflib.URIRef(URI_BASE + "platform/" + urllib.parse.quote_plus(_platform)))
            platform.add(rdflib.RDF.type, SSN.Platform)
            platform.add(rdflib.RDFS.label, rdflib.Literal(item["platform long name"]))
            # r.add(DD.platform, platform)

        if "instrument" in item and item["instrument"] is not None:
            _instrument = item["instrument"]
            instrument = g.resource(
                rdflib.URIRef(URI_BASE + "instrument/" + urllib.parse.quote_plus(_instrument)))
            instrument.add(rdflib.RDF.type, DD.System)
            instrument.add(rdflib.RDF.type, DD.Sensor)
            if platform is not None:
                instrument.add(SSN.onPlatform, platform)
                platform.add(SSN.attachedSystem, instrument)
            instrument.add(rdflib.RDFS.label, rdflib.Literal(item["instrument long name"]))
            # r.add(DD.instrument, instrument)

            if measurement is not None:
                instrument.add(SSN.observes, measurement)

        for keyword in item["keywords"].split(";"):
            r.add(DC.subject, rdflib.Literal(keyword))

        # AKA Deployment?
        if "platform instrument" in item:
            _deployment = item["platform instrument"]
            deployment = g.resource(rdflib.URIRef(
                URI_BASE + "platform-instrument/" + urllib.parse.quote_plus(_deployment)))
            deployment.add(rdflib.RDF.type, SSN.Deployment)
            deployment.add(rdflib.RDFS.label, rdflib.Literal(_deployment))

            r.add(DD.hasDeployment, deployment)

            if instrument is not None:
                deployment.add(SSN.deployedSystem, instrument)
                instrument.add(SSN.hasDeployment, deployment)

            if platform is not None:
                deployment.add(SSN.deployedOnPlatform, platform)
                platform.add(SSN.inDeployment, deployment)

    g.serialize("datafields.ttl", format="turtle")

csv_file = "resources/aesir_2016_11_02.xml"

tree = etree.parse(csv_file)
root = tree.getroot()
docs = tree.findall('.//doc')
records = []

time_intervals = set()
spatial_resolutions = set()
measurements = set()

for doc in docs:
    g3ID = doc.find("str[@name='dataFieldId']")
    measurement_nodes = doc.findall("arr[@name='dataFieldMeasurement']/str")
    measurements = str.join(';', [node.text for node in measurement_nodes])

    product_gcmd_id = doc.find("str[@name='dataProductGcmdEntryId']")
    sds_name = doc.find("str[@name='dataFieldSdsName']")

    keyword_nodes = doc.findall("arr[@name='dataFieldKeywords']/str")
    keywords = str.join(';', [node.text for node in keyword_nodes])

    processingLevel = doc.find("str[@name='dataProductProcessingLevel']")
    timeInterval = doc.find("str[@name='dataProductTimeInterval']")
    spatialResolution = doc.find("str[@name='dataProductSpatialResolution']")

    instrument = doc.find("str[@name='dataProductInstrumentShortName']")
    platform = doc.find("str[@name='dataProductPlatformShortName']")
    platform_instrument = doc.find("str[@name='dataProductPlatformInstrument']")

    platform_long_name = doc.find("str[@name='dataProductPlatformLongName']")
    instrument_long_name = doc.find("str[@name='dataProductInstrumentLongName']")

    product = doc.find("str[@name='dataProductShortName']")
    product_version = doc.find("str[@name='dataProductVersion']")
    versioned_product = doc.find("str[@name='dataProductId']")
    # product_long_name

    if g3ID is not None:
        record = {'id': g3ID.text,
                  "product gcmd id": product_gcmd_id.text if product_gcmd_id is not None else None,
                  "sds name": sds_name.text if sds_name is not None else None,
                  "measurements": measurements if measurements is not None else [],
                  "time interval": timeInterval.text if timeInterval is not None else None,
                  "spatial resolution": spatialResolution.text if spatialResolution is not None else None,
                  "keywords": keywords if keywords is not None else [],
                  "processing level": processingLevel.text if processingLevel is not None else None,
                  "instrument": instrument.text if instrument is not None else None,
                  "platform": platform.text if platform is not None else None,
                  "platform instrument": platform_instrument.text if platform_instrument is not None else None,
                  "platform long name": platform_long_name.text if platform_long_name is not None else None,
                  "instrument long name": instrument_long_name.text if instrument_long_name is not None else None,
                  "versioned product": versioned_product.text if versioned_product is not None else None,
                  "product": product.text if product is not None else None,
                  "product version": product_version.text if product_version is not None else None}
        records.append(record)

    time_intervals.add(timeInterval.text)
    spatial_resolutions.add(spatialResolution.text)

#write_csv(records)
write_rdf(records)

print(time_intervals)
print(spatial_resolutions)