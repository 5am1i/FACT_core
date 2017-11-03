import logging
import sys

from time import time

from storage.db_interface_common import MongoInterfaceCommon
from helperFunctions.dataConversion import unify_string_list, list_to_unified_string_list, string_list_to_list


class CompareDbInterface(MongoInterfaceCommon):

    def _setup_database_mapping(self):
        super()._setup_database_mapping()
        self.compare_results = self.main.compare_results

    def add_compare_result(self, compare_result):
        compare_result['_id'] = self._calculate_compare_result_id(compare_result)
        compare_result["submission_date"] = time()
        try:
            self.compare_results.delete_one({'_id': compare_result['_id']})
        except Exception:
            pass
        self.compare_results.insert_one(compare_result)
        logging.info("compare result added to db: {}".format(compare_result['_id']))

    def get_compare_result(self, compare_id):
        compare_id = unify_string_list(compare_id)
        err = self.object_existence_quick_check(compare_id)
        if err is None:
            compare_result = self.compare_results.find_one(compare_id)
            if compare_result:
                logging.debug("got compare result from db: {}".format(compare_id))
                return compare_result
            else:
                logging.debug("compare result not found in db: {}".format(compare_id))
                return None
        else:
            return err

    def object_existence_quick_check(self, compare_id):
        uids = string_list_to_list(compare_id)
        err = None
        for uid in uids:
            if not self.existence_quick_check(uid):
                err = "{} not found in database".format(uid)
        return err

    def compare_result_is_in_db(self, compare_id):
        compare_result = self.compare_results.find_one(unify_string_list(compare_id))
        return True if compare_result else False

    def delete_old_compare_result(self, compare_id):
        try:
            self.compare_results.remove({"_id": unify_string_list(compare_id)})
            logging.debug("old compare result deleted: {}".format(compare_id))
        except Exception as e:
            logging.warning("Could not delete old compare result: {} {}".format(sys.exc_info()[0].__name__, e))

    @staticmethod
    def _calculate_compare_result_id(compare_result):
        general_keys = list(compare_result['general'].keys())
        uids = list(compare_result['general'][general_keys[0]].keys())
        comp_id = list_to_unified_string_list(uids)
        return comp_id

    def page_compare_results(self, skip=0, limit=0):
        db_entries = self.compare_results.find({'submission_date': {"$gt": 1}}, {"general.hid": 1, "submission_date": 1}, skip=skip, limit=limit, sort=[("submission_date", -1)])
        all_previous_results = [(item["_id"], item["general"]["hid"], item["submission_date"]) for item in db_entries]
        return [compare for compare in all_previous_results if not self.object_existence_quick_check(compare[0])]
