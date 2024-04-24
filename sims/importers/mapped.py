from djson.models import ModelType
from sims.importers import Importer
from sims.models import Project, Sample, Pool
from django.utils import timezone

class MappedImporter(Importer):
    # def __init__(self, submission, importer):
    #     self.submission = submission
    #     self.importer = importer
    @staticmethod
    def map_data(mapping, data={}, row_data={}, array_prefix=''):
        # raise Exception(mapping.keys(), row_data, array_prefix)
        result = {}
        for k, v in mapping.items():
            if isinstance(v, dict):
                result[k] = MappedImporter.map_data(v, data, row_data, array_prefix)
            else:
                if '.' in v:
                    parts = v.split('.')
                    if parts[0] == array_prefix and len(parts) == 2:
                        result[k] = row_data.get(parts[1])
                else:
                    result[k] = data.get(v)
        return result
    def get_type(self, model):
        if self.importer.model_type:
            type_id = self.importer.model_type.metadata.get(model, None)
            return ModelType.objects.filter(id=type_id).first()
    def get_array_data(self, model): # takes 'pool', 'sample', or 'project'
        # { "pool": { "type": "array", "source": null, "mapping": {} }, "sample": { "type": "array", "source": "samples", "mapping": { "data": { "i5": "samples[].fragment_size", "i7": "samples[].special_instructions" }, "name": "samples[].sample_name" } }, "run_type": "runtype" }
        mapping = self.importer.config.get(model)
        if not mapping or 'mapping' not in mapping:
            return []
        data = []
        if mapping.get('type') == 'array' and mapping.get('source', None):
            source = mapping['source']
            array = self.submission.data.get(source)
            for row in array:
                mapped = MappedImporter.map_data(mapping.get('mapping', {}), self.submission.data, row, array_prefix=source)
                mapped['submission_data'] = row
                data.append(mapped)
        return data
    def pool_samples(self):
        pass
        # for pool in pools:
        #     pool_samples = []
        #     for sample in samples:
        #         if pool.data.get(pool_id_column) and sample.data.get(pool_id_column) == pool.data.get(pool_id_column):
        #             pool_samples.append(sample)
        #     pool.samples.add(*pool_samples)
    def get_pools(self):
        from sims.models import Pool
        pool_data = self.get_array_data('pool')
        pools = []
        model_type = self.get_type('pool')
        for fields in pool_data:
            fields['project'] = self.project
            fields['submission'] = self.submission
            fields['type'] = model_type
            pool = Pool(**fields)
            pool.unique_id = '{}_{}'.format(self.project.id, pool.name)
            pools.append(pool)
        return pools
    def get_samples(self):
        from sims.models import Sample
        sample_data = self.get_array_data('sample')
        samples = []
        model_type = self.get_type('sample')
        for fields in sample_data:
            fields['project'] = self.project
            fields['submission'] = self.submission
            fields['type'] = model_type
            sample = Sample(**fields)
            sample.id = '{}_{}'.format(self.project.id, sample.name)
            samples.append(sample)
        return samples
    def process(self):
        self.project = self.get_project()
        samples = self.get_samples()
        pools = self.get_pools()
        # raise Exception(self.project, pools, samples)
        self.project.save()
        pools = Pool.objects.bulk_create(pools)
        samples = Sample.objects.bulk_create(samples)
        # pool_samples(project, pools, samples)
        self.submission.importer = self.importer
        self.submission.processed = timezone.now()
        # self.data = self.project.submission_data
        self.submission.save()
        # libraries = Library.objects.bulk_create(libraries)
        return (self.project, pools, samples)
"""
def import_submission(submission):
    
    data = submission.data
    pools, samples = [], []
    if 'pools' in data and isinstance(data['pools'], list):
        pools = get_pools(project, submission)
    if 'samples' in data and isinstance(data['samples'], list):
        samples = get_samples(project, submission)
    if 'libraries' in data and isinstance(data['libraries'], list):
        samples = get_libraries(project, submission)
    return (project, pools, samples)

def get_pools(project, submission, field_map=pool_field_map):
    schema = submission.schema
    data = submission.data
    pools = []
    for row in data[field_map['row']]:
        fields = {key: row[val] for key, val in field_map['fields'].items() if val}
        fields['submission_data'] = row
        pool = Pool(**fields)
        pool.name = '{}_{}'.format(project.id, pool.name)
        pool.submission = submission
        pool.project = project
        pools.append(pool)
    return pools

def get_samples(project, submission, field_map=sample_field_map):
    # need to handle pools
    schema = submission.schema
    data = submission.data
    samples = []
    for row in data[field_map['row']]:
        fields = {key: row[val] for key, val in field_map['fields'].items()}
        fields['submission_data'] = row
        fields['project'] = project
        sample = Sample(**fields)
        sample.id = '{}_{}'.format(project.id,sample.name)
        sample.submission = submission
        samples.append(sample)
    return samples

def get_libraries(project, submission, field_map=library_field_map):
    # This is just for testing, and will probably go as libraries may become just a type of sample
    schema = submission.schema
    data = submission.data
    samples = []
    # libraries = []
    for row in data[field_map['row']]:
        fields = {key: row[val] for key, val in field_map['fields'].items()}
        fields['submission_data'] = row
        fields['project'] = project
        fields['physical_type'] = Sample.TYPE_LIBRARY
        sample = Sample(**fields)
        sample.submission = submission
        sample.id = '{}_{}'.format(project.id,sample.name)
        samples.append(sample)
        # library = Library(id=sample.id, sample=sample)
        # libraries.append(library)
    return samples
    """