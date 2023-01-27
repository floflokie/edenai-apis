from typing import Optional
from pydantic import BaseModel
import pytest

from edenai_apis.interface import list_features, list_providers
from edenai_apis.loaders.data_loader import (
    load_class,
    load_dataclass,
    load_info_file,
    load_key,
    load_output,
    load_provider_subfeature_info,
    load_samples,
    load_subfeature
)
from edenai_apis.tests.conftest import global_features, global_providers, without_async, only_async


def _get_feature_subfeature_phase():
    load_feature_list = list_features()
    list_without_provider = list(set([(f, s, ph[0] if ph else "") for (p, f, s, *ph) in load_feature_list]))
    detailed_providers_list = []
    for feature, subfeature, *phase in list_without_provider:
        detailed_params = pytest.param(
            feature,
            subfeature,
            phase[0] if phase else "",
            marks=[
                getattr(pytest.mark, feature),
                getattr(pytest.mark, subfeature)],
        )
        detailed_providers_list.append(detailed_params)
    return detailed_providers_list


class TestLoadKey:
    @pytest.mark.parametrize(
        ('provider'),
        global_providers()
    )
    def test_load_key_of_valid_provider(self, provider: str):
        data = load_key(provider, False)
        assert isinstance(data, dict), f"No settings.json file found for {provider}"


class TestLoadClass:
    @pytest.mark.parametrize(
        ('provider'),
        global_providers()
    )
    def test_load_class_with_all_provider(self, provider: Optional[str]):
        klass = load_class(provider)

        assert klass is not None

    def test_load_class_with_bad_provider(self):
        with pytest.raises(ValueError, match="No ProviderInterface class implemented for provider:"):
            load_class('NotAProvider')

    def test_load_class_with_none_provider(self):
        klass = load_class()

        len_klass = len(klass)
        nb_providers = len(list_providers())
        assert len_klass == nb_providers


class TestLoadDataclass:
    @pytest.mark.parametrize(
        ('feature', 'subfeature', 'phase'),
        _get_feature_subfeature_phase()
    )
    def test_load_dataclass(self, feature, subfeature, phase):
        if phase == 'create_project':
            pytest.skip("image-search-create_project because this method don't need to return a dataclass")

        dataclass = load_dataclass(feature, subfeature, phase)

        assert issubclass(dataclass, BaseModel)


class TestLoadInfoFile:
    @pytest.mark.parametrize(
        ('provider'),
        global_providers()
    )
    def test_load_info_file_with_one_provider(self, provider):
        info = load_info_file(provider)

        assert isinstance(info, dict)


class TestLoadProviderSubfeatureInfo:
    @pytest.mark.parametrize(
        ('provider', 'feature', 'subfeature', 'phase'),
        global_features(return_phase=True)
    )
    def test_load_info_subfeature_provider(self, provider, feature, subfeature, phase):
        info = load_provider_subfeature_info(provider, feature, subfeature, phase)

        assert isinstance(info, dict)
        assert info.get('version')


class TestLoadOutput:
    @pytest.mark.parametrize(
        ('provider', 'feature', 'subfeature', 'phase'),
        global_features(return_phase=True)
    )
    def test_load_output_valid_paramters(self, provider, feature, subfeature, phase):
        #skip create and delete method
        if "create" in phase or "delete" in phase or "upload" in phase:
            pytest.skip("create, delete and upload phase don't have a output.json")

        output = load_output(provider, feature, subfeature, phase)

        assert isinstance(output, dict), "output should be a dict"
        try:
            output['original_response']
            output['standardized_response']
        except KeyError:
            pytest.fail("Original_response and standradized_response not found")


class TestLoadSubfeature:
    @pytest.mark.parametrize(
        ('provider', 'feature', 'subfeature', 'phase'),
        global_features(without_async, return_phase=True)
    )
    def test_load_subfeature_sync_subfeature(self, provider, feature, subfeature, phase):
        method_subfeature = load_subfeature(provider, feature, subfeature, phase)

        expected_name = f'{feature}__{subfeature}'
        if phase:
            expected_name += f'__{phase}'

        assert callable(method_subfeature)
        assert method_subfeature.__name__ == expected_name


    @pytest.mark.parametrize(
        ('provider', 'feature', 'subfeature'), 
        global_features(only_async)
    )
    def test_load_subfeature_sync_subfeature_get_job_result(self, provider, feature, subfeature):
        method_subfeature = load_subfeature(provider, feature, subfeature, 'get_job_result')

        expected_name = f'{feature}__{subfeature}__get_job_result'

        assert callable(method_subfeature)
        assert method_subfeature.__name__ == expected_name


    @pytest.mark.parametrize(
        ('provider', 'feature', 'subfeature'),
        global_features(only_async)
    )
    def test_load_subfeature_sync_subfeature_launch_job(self, provider, feature, subfeature):
        method_subfeature = load_subfeature(provider, feature, subfeature, 'launch_job')

        expected_name = f'{feature}__{subfeature}__launch_job'

        assert callable(method_subfeature)
        assert method_subfeature.__name__ == expected_name

class TestLoadSamples:
    @pytest.mark.parametrize(
        ('feature', 'subfeature', 'phase'),
        _get_feature_subfeature_phase()
    )
    def test_load_sample_valid_parameters(self, feature, subfeature, phase):
        if phase == 'create_project':
            pytest.skip("image-search-create_project because this method don't need arguments")

        args = load_samples(feature, subfeature, phase)

        assert isinstance(args, dict), "Arguments should be a dictionnary"