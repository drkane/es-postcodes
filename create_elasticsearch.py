import argparse
from elasticsearch import Elasticsearch


INDEXES = [
    {
        "name": "postcode",
        "mapping": [
            ("postcode", {
                    "properties": {
                        "boundary": {"type": "geo_shape"}
                    }
                }
            ),
            ("code", {
                    "properties": {
                        "boundary": {"type": "geo_shape"}
                    }
                }
            ),
        ]
    }
]

def main():

    parser = argparse.ArgumentParser(description='Setup elasticsearch indexes.')
    parser.add_argument('--reset', action='store_true',
                        help='If set, any existing indexes will be deleted and recreated.')
    args = parser.parse_args()

    es = Elasticsearch()

    for i in INDEXES:
        if es.indices.exists( i["name"]  ) and args.reset:
            print("[elasticsearch] deleting '%s' index..." % ( i["name"]  ))
            res = es.indices.delete(index =  i["name"]  )
            print("[elasticsearch] response: '%s'" % (res))
        print("[elasticsearch] creating '%s' index..." % ( i["name"]  ))
        res = es.indices.create(index =  i["name"]  )

        if "mapping" in i:
            for mapping in i["mapping"]:
                res = es.indices.put_mapping(mapping[0], mapping[1], index= i["name"]   )
                print("[elasticsearch] set mapping on %s index, %s type" % ( i["name"], mapping[0]  ))

if __name__ == '__main__':
    main()
