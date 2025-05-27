import logging
import pandas as pd
from parser.core_parsing import parse_chunks_to_structured_data
from parser.constants import COLUMN_HEADERS

_log = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    test_chunks = [
        "Postavy:\nANDREJ\nEVA\nPETER KOLAR\nEVA MALA\n\nNINA\nJAN\nMARTIN\nPETER\nJOZO\nJAN4\nJUANA DE ARAG\nDE LA PARRA\n\n00:01:33----------\n00:01:33\tANDREJ\t(dychy) Kde si bola?\nEVA\tNebola som doma.\nPETER KOLAR\t00:02:12\tPridem zajtra\nJAN,MARTIN,PETER,JOZO\tNeprideme tam ani my\n----------\nJUANA DE ARAG\tKde si\nJAN4\tNeviem\nDE LA PARRA\tJa som stale doma\nEVA MALA\t00:03:40\tNebolo to mozne"
    ]
    parsed_data = parse_chunks_to_structured_data(test_chunks)
    print("\nParsed Data:")
    if parsed_data:
        df_test = pd.DataFrame(parsed_data, columns=COLUMN_HEADERS)
        print(df_test.to_string())
    else:
        print("No data parsed.")
