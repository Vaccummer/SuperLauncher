#include <bit7z/bitfilecompressor.hpp>
#include <bit7z/bitfileextractor.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include <pybind11/complex.h>
#include <vector>
#include <string>
#include <iostream>
#include <type_traits>
#include <windows.h>

namespace py = pybind11;
using f_ptr = std::shared_ptr<py::function>;
using int_ptr = std::shared_ptr<uint64_t>;
using bool_ptr = std::shared_ptr<bool>;
using float_ptr = std::shared_ptr<float>;
using str_ptr = std::shared_ptr<std::string>;
bit7z::Bit7zLibrary lib{"7z.dll"};

enum class ZipperErrorCode
{
    success = 0,
    FilterNotSpecified = -1,
    FormatFeatureNotSupported = -2,
    IndicesNotSpecified = -3,
    InvalidArchivePath = -4,
    InvalidOutputBufferSize = -5,
    InvalidCompressionMethod = -6,
    InvalidDictionarySize = -7,
    InvalidIndex = -8,
    InvalidWordSize = -9,
    ItemIsAFolder = -10,
    ItemMarkedAsDeleted = -11,
    NoMatchingItems = -12,
    NoMatchingSignature = -13,
    NonEmptyOutputBuffer = -14,
    NullOutputBuffer = -15,
    RequestedWrongVariantType = -16,
    UnsupportedOperation = -17,
    UnsupportedVariantType = -18,
    WrongUpdateMode = -19,
    InvalidZipPassword = -20,
    UnknownError = -21,
    IDNotExist = -22,
};

void total_size_set(int_ptr ptr, uint64_t size)
{
    *ptr = size;
}
bool taskControl(bool_ptr ptr, uint64_t size1)
{
    return *ptr;
}
void RatioCB(f_ptr py_cb, float cb_per_interval, float_ptr progress_ptr, int_ptr total_ptr, uint64_t input_size, uint64_t output_size)
{
    if (*total_ptr == 0)
    {
        return;
    }
    float progress = static_cast<float>(input_size) / (*total_ptr);
    float gap = progress - *progress_ptr;
    if (gap > cb_per_interval)
    {
        (*py_cb)(progress);
        *progress_ptr = progress;
    }
}

ZipperErrorCode GetError(int bit_error_code)
{
    switch (static_cast<bit7z::BitError>(bit_error_code))
    {
    case bit7z::BitError::FilterNotSpecified:
        return ZipperErrorCode::FilterNotSpecified;
    case bit7z::BitError::FormatFeatureNotSupported:
        return ZipperErrorCode::FormatFeatureNotSupported;
    case bit7z::BitError::IndicesNotSpecified:
        return ZipperErrorCode::IndicesNotSpecified;
    case bit7z::BitError::InvalidArchivePath:
        return ZipperErrorCode::InvalidArchivePath;
    case bit7z::BitError::InvalidOutputBufferSize:
        return ZipperErrorCode::InvalidOutputBufferSize;
    case bit7z::BitError::InvalidCompressionMethod:
        return ZipperErrorCode::InvalidCompressionMethod;
    case bit7z::BitError::InvalidDictionarySize:
    case bit7z::BitError::InvalidIndex:
        return ZipperErrorCode::InvalidIndex;
    case bit7z::BitError::InvalidWordSize:
        return ZipperErrorCode::InvalidWordSize;
    case bit7z::BitError::ItemIsAFolder:
        return ZipperErrorCode::ItemIsAFolder;
    case bit7z::BitError::NonEmptyOutputBuffer:
        return ZipperErrorCode::NonEmptyOutputBuffer;
    case bit7z::BitError::NullOutputBuffer:
        return ZipperErrorCode::NullOutputBuffer;
    case bit7z::BitError::InvalidZipPassword:
        return ZipperErrorCode::InvalidZipPassword;
    case bit7z::BitError::NoMatchingItems:
        return ZipperErrorCode::NoMatchingItems;
    case bit7z::BitError::RequestedWrongVariantType:
        return ZipperErrorCode::RequestedWrongVariantType;
    case bit7z::BitError::UnsupportedOperation:
        return ZipperErrorCode::UnsupportedOperation;
    case bit7z::BitError::UnsupportedVariantType:
        return ZipperErrorCode::UnsupportedVariantType;
    case bit7z::BitError::ItemMarkedAsDeleted:
        return ZipperErrorCode::ItemMarkedAsDeleted;
    case bit7z::BitError::WrongUpdateMode:
        return ZipperErrorCode::WrongUpdateMode;
    case bit7z::BitError::NoMatchingSignature:
        return ZipperErrorCode::NoMatchingSignature;
    default:
        return ZipperErrorCode::UnknownError;
    }
}

class ZIPmanager
{
private:
    bit7z::BitFileCompressor get_compressor(std::string format)
    {
        if (format == "zip")
        {
            return bit7z::BitFileCompressor{lib, bit7z::BitFormat::Zip};
        }
        else if (format == "7z")
        {
            return bit7z::BitFileCompressor{lib, bit7z::BitFormat::SevenZip};
        }
        else if (format == "bz2")
        {
            return bit7z::BitFileCompressor{lib, bit7z::BitFormat::BZip2};
        }
        else if (format == "xz")
        {
            return bit7z::BitFileCompressor{lib, bit7z::BitFormat::Xz};
        }
        else if (format == "tar")
        {
            return bit7z::BitFileCompressor{lib, bit7z::BitFormat::Tar};
        }
        else if (format == "gz")
        {
            return bit7z::BitFileCompressor{lib, bit7z::BitFormat::GZip};
        }
        else
        {
            return bit7z::BitFileCompressor{lib, bit7z::BitFormat::Zip};
        }
    }

    bit7z::BitFileExtractor get_extractor(std::string format)
    {
        if (format == "zip")
        {
            return bit7z::BitFileExtractor{lib, bit7z::BitFormat::Zip};
        }
        else if (format == "7z")
        {
            return bit7z::BitFileExtractor{lib, bit7z::BitFormat::SevenZip};
        }
        else if (format == "bz2")
        {
            return bit7z::BitFileExtractor{lib, bit7z::BitFormat::BZip2};
        }
        else if (format == "xz")
        {
            return bit7z::BitFileExtractor{lib, bit7z::BitFormat::Xz};
        }
        else if (format == "tar")
        {
            return bit7z::BitFileExtractor{lib, bit7z::BitFormat::Tar};
        }
        else if (format == "gz")
        {
            return bit7z::BitFileExtractor{lib, bit7z::BitFormat::GZip};
        }
        else
        {
            return bit7z::BitFileExtractor{lib, bit7z::BitFormat::Zip};
        }
    }

public:
    std::unordered_map<uint64_t, bool_ptr> ID_ptr_map;
    ZIPmanager() : ID_ptr_map({})
    {
    }

    ZipperErrorCode compress(uint64_t ID,
                             std::vector<std::string> srcs,
                             std::string output_path,
                             std::string format,
                             std::wstring password,
                             float cb_per_interval,
                             uint64_t threads,
                             py::function file_cb,
                             py::function progress_cb)
    {
        bit7z::BitFileCompressor compressor = get_compressor(format);
        compressor.setThreadsCount(threads);
        bit7z::tstring t_password = bit7z::to_tstring(password);
        if (!t_password.empty())
        {
            compressor.setPassword(t_password);
        }

        bool_ptr control_ptr = std::make_shared<bool>(true);
        float_ptr progress_ptr = std::make_shared<float>(0);
        int_ptr total_size_ptr = std::make_shared<uint64_t>(0);
        f_ptr cb_py_ptr = std::make_shared<py::function>(progress_cb);
        bit7z::TotalCallback t_cb = std::bind(total_size_set, total_size_ptr, std::placeholders::_1);
        bit7z::ProgressCallback p_cb = std::bind(taskControl, control_ptr, std::placeholders::_1);
        bit7z::RatioCallback r_cb = std::bind(RatioCB, cb_py_ptr, cb_per_interval, progress_ptr, total_size_ptr, std::placeholders::_1, std::placeholders::_2);

        compressor.setTotalCallback(t_cb);
        compressor.setProgressCallback(p_cb);
        compressor.setFileCallback(file_cb);
        compressor.setRatioCallback(r_cb);
        compressor.setStoreSymbolicLinks(true);
        try
        {
            ID_ptr_map[ID] = control_ptr;
            compressor.compress(srcs, output_path);
            if (ID_ptr_map.find(ID) != ID_ptr_map.end())
            {
                ID_ptr_map.erase(ID);
            }
            return ZipperErrorCode::success;
        }
        catch (bit7z::BitException &ex)
        {
            if (ID_ptr_map.find(ID) != ID_ptr_map.end())
            {
                ID_ptr_map.erase(ID);
            }
            return GetError(ex.code().value());
        }
    }

    ZipperErrorCode decompress(uint64_t ID,
                               std::string src,
                               std::string output_dir,
                               std::string format,
                               std::wstring password,
                               float cb_per_interval,
                               py::function file_cb,
                               py::function progress_cb)
    {
        bit7z::BitFileExtractor extractor = get_extractor(format);

        bit7z::tstring t_password = bit7z::to_tstring(password);
        if (!t_password.empty())
        {
            extractor.setPassword(t_password);
        }

        bool_ptr control_ptr = std::make_shared<bool>(true);
        float_ptr progress_ptr = std::make_shared<float>(0);
        int_ptr total_size_ptr = std::make_shared<uint64_t>(0);
        f_ptr cb_py_ptr = std::make_shared<py::function>(progress_cb);
        bit7z::TotalCallback t_cb = std::bind(total_size_set, total_size_ptr, std::placeholders::_1);
        bit7z::ProgressCallback p_cb = std::bind(taskControl, control_ptr, std::placeholders::_1);
        bit7z::RatioCallback r_cb = std::bind(RatioCB, cb_py_ptr, cb_per_interval, progress_ptr, total_size_ptr, std::placeholders::_1, std::placeholders::_2);

        extractor.setTotalCallback(t_cb);
        extractor.setProgressCallback(p_cb);
        extractor.setFileCallback(file_cb);
        extractor.setRatioCallback(r_cb);
        try
        {
            ID_ptr_map[ID] = control_ptr;
            extractor.extract(src, output_dir);
            if (ID_ptr_map.find(ID) != ID_ptr_map.end())
            {
                ID_ptr_map.erase(ID);
            }
            return ZipperErrorCode::success;
        }
        catch (bit7z::BitException &ex)
        {
            if (ID_ptr_map.find(ID) != ID_ptr_map.end())
            {
                ID_ptr_map.erase(ID);
            }
            return GetError(ex.code().value());
        }
    }

    std::vector<uint64_t> getIDs()
    {
        std::vector<uint64_t> ids = {};
        for (const auto &pair : ID_ptr_map)
        {
            ids.push_back(pair.first);
        }
        return ids;
    };

    ZipperErrorCode terminate(uint64_t ID_f)
    {
        if (ID_ptr_map.find(ID_f) != ID_ptr_map.end())
        {
            *ID_ptr_map[ID_f] = false;
            ID_ptr_map.erase(ID_f);
            return ZipperErrorCode::success;
        }
        return ZipperErrorCode::IDNotExist;
    };
};

PYBIND11_MODULE(ZIPmanager, m)
{
    py::class_<ZIPmanager>(m, "ZIPmanager")
        .def(py::init<>())
        .def("compress", &ZIPmanager::compress, "Compress files", py::arg("ID"), py::arg("srcs"), py::arg("output_path"), py::arg("format"), py::arg("password"), py::arg("cb_per_interval"), py::arg("threads"), py::arg("file_cb"), py::arg("progress_cb"))
        .def("decompress", &ZIPmanager::decompress, "Decompress files", py::arg("ID"), py::arg("src"), py::arg("output_dir"), py::arg("format"), py::arg("password"), py::arg("cb_per_interval"), py::arg("file_cb"), py::arg("progress_cb"))
        .def("terminate", &ZIPmanager::terminate, "Terminate a task", py::arg("ID_f"))
        .def("getIDs", &ZIPmanager::getIDs, "Get all IDs");
    pybind11::enum_<ZipperErrorCode>(m, "ZipperErrorCode")
        .value("success", ZipperErrorCode::success)
        .value("FilterNotSpecified", ZipperErrorCode::FilterNotSpecified)
        .value("FormatFeatureNotSupported", ZipperErrorCode::FormatFeatureNotSupported)
        .value("IndicesNotSpecified", ZipperErrorCode::IndicesNotSpecified)
        .value("InvalidArchivePath", ZipperErrorCode::InvalidArchivePath)
        .value("InvalidOutputBufferSize", ZipperErrorCode::InvalidOutputBufferSize)
        .value("InvalidCompressionMethod", ZipperErrorCode::InvalidCompressionMethod)
        .value("InvalidDictionarySize", ZipperErrorCode::InvalidDictionarySize)
        .value("InvalidIndex", ZipperErrorCode::InvalidIndex)
        .value("InvalidWordSize", ZipperErrorCode::InvalidWordSize)
        .value("ItemIsAFolder", ZipperErrorCode::ItemIsAFolder)
        .value("ItemMarkedAsDeleted", ZipperErrorCode::ItemMarkedAsDeleted)
        .value("NoMatchingItems", ZipperErrorCode::NoMatchingItems)
        .value("NoMatchingSignature", ZipperErrorCode::NoMatchingSignature)
        .value("NonEmptyOutputBuffer", ZipperErrorCode::NonEmptyOutputBuffer)
        .value("NullOutputBuffer", ZipperErrorCode::NullOutputBuffer)
        .value("RequestedWrongVariantType", ZipperErrorCode::RequestedWrongVariantType)
        .value("UnsupportedOperation", ZipperErrorCode::UnsupportedOperation)
        .value("UnsupportedVariantType", ZipperErrorCode::UnsupportedVariantType)
        .value("WrongUpdateMode", ZipperErrorCode::WrongUpdateMode)
        .value("InvalidZipPassword", ZipperErrorCode::InvalidZipPassword)
        .value("UnknownError", ZipperErrorCode::UnknownError)
        .value("IDNotExist", ZipperErrorCode::IDNotExist)
        .export_values();
}
