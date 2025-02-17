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

namespace py = pybind11;
using int_ptr = std::shared_ptr<uint64_t>;
using bool_ptr = std::shared_ptr<bool>;
using str_ptr = std::shared_ptr<std::string>;
bit7z::Bit7zLibrary lib{"7z.dll"};

void total_size_set(int_ptr ptr, uint64_t size)
{
    *ptr = size;
}

void progress_cb(int_ptr size_n_ptr, uint64_t size_n, uint64_t total_t)
{
    *size_n_ptr = size_n;
}

void py_pg_cb(int_ptr total_ptr, int_ptr size_n_ptr, bool_ptr exit_ptr, bool_ptr conduct, bool_ptr manual_cancel_ptr, uint64_t interval, py::function pg_cb)
{
    while (*size_n_ptr < *total_ptr && !*exit_ptr)
    {
        if (*total_ptr != 1)
        {
            double progress = (double)*size_n_ptr / *total_ptr;
            bool sign_f = pg_cb(progress).cast<bool>();
            if (!sign_f)
            {
                *conduct = false;
                *manual_cancel_ptr = true;
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(interval));
    }
}

bool pg_control(bool_ptr conduct_ptr, uint64_t progress)
{
    return *conduct_ptr;
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
    ZIPmanager()
    {
    }

    int compress(std::vector<std::string> srcs,
                 std::string output_path,
                 std::string format,
                 std::string password,
                 uint64_t interval,
                 uint64_t threads,
                 py::function pg_cb,
                 py::function filename_cb)
    {
        int_ptr total_size_ptr = std::make_shared<uint64_t>(1);
        int_ptr size_n_ptr = std::make_shared<uint64_t>(0);
        bool_ptr exit_ptr = std::make_shared<bool>(false);
        bool_ptr conduct_ptr = std::make_shared<bool>(true);
        bool_ptr manual_cancel_ptr = std::make_shared<bool>(false);
        std::thread pg_thread = std::thread(py_pg_cb, total_size_ptr, size_n_ptr, exit_ptr, conduct_ptr, manual_cancel_ptr, interval, pg_cb);
        try
        {
            bit7z::BitFileCompressor compressor = get_compressor(format);
            compressor.setThreadsCount(threads);
            if (!password.empty())
            {
                compressor.setPassword(password);
            }
            bit7z::FileCallback fc = filename_cb;
            bit7z::RatioCallback pc = std::bind(progress_cb, size_n_ptr, std::placeholders::_1, std::placeholders::_2);
            bit7z::TotalCallback tc = std::bind(total_size_set, total_size_ptr, std::placeholders::_1);
            bit7z::ProgressCallback pc_cb = std::bind(pg_control, conduct_ptr, std::placeholders::_1);
            compressor.setRatioCallback(pc);
            compressor.setTotalCallback(tc);
            compressor.setFileCallback(fc);
            compressor.setProgressCallback(pc_cb);
            compressor.compress(srcs, output_path);
            *exit_ptr = true;
            pg_thread.join();
            if (*manual_cancel_ptr)
            {
                return -7;
            }
            return 0;
        }
        catch (const bit7z::BitException &ex)
        {
            if (*manual_cancel_ptr)
            {
                return -7;
            }
            std::cerr << "Error_Code: " << ex.code().value() << std::endl;
            std::cerr << "Error_Message: " << ex.what() << std::endl;
            *exit_ptr = true;
            pg_thread.join();
            return ex.code().value();
        }
    };

    int decompress(std::string src,
                   std::string output_dir,
                   std::string format,
                   std::string password,
                   uint64_t interval,
                   uint64_t threads,
                   py::function pg_cb,
                   py::function filename_cb)
    {
        int_ptr total_size_ptr = std::make_shared<uint64_t>(1);
        int_ptr size_n_ptr = std::make_shared<uint64_t>(0);
        bool_ptr exit_ptr = std::make_shared<bool>(false);
        bool_ptr conduct_ptr = std::make_shared<bool>(true);
        bool_ptr manual_cancel_ptr = std::make_shared<bool>(false);
        std::thread pg_thread = std::thread(py_pg_cb, total_size_ptr, size_n_ptr, exit_ptr, conduct_ptr, manual_cancel_ptr, interval, pg_cb);
        try
        {
            bit7z::BitFileExtractor extractor = get_extractor(format);
            if (!password.empty())
            {
                extractor.setPassword(password);
            }
            // extractor.setThreadsCount(threads);
            bit7z::FileCallback fc = filename_cb;
            bit7z::RatioCallback pc = std::bind(progress_cb, size_n_ptr, std::placeholders::_1, std::placeholders::_2);
            bit7z::TotalCallback tc = std::bind(total_size_set, total_size_ptr, std::placeholders::_1);
            bit7z::ProgressCallback pg_cb = std::bind(pg_control, conduct_ptr, std::placeholders::_1);
            extractor.setRatioCallback(pc);
            extractor.setTotalCallback(tc);
            extractor.setFileCallback(fc);
            extractor.setProgressCallback(pg_cb);
            extractor.extract(src, output_dir);
            *exit_ptr = true;
            pg_thread.join();
            if (*manual_cancel_ptr)
            {
                return -7;
            }
            return 0;
        }
        catch (const bit7z::BitException &ex)
        {
            if (*manual_cancel_ptr)
            {
                return -7;
            }
            std::cerr << "Error_Message: " << ex.what() << std::endl;
            std::cerr << "Error_Code: " << ex.code().value() << std::endl;
            *exit_ptr = true;
            pg_thread.join();
            return ex.code().value();
        }
    };
};

PYBIND11_MODULE(ZIPmanager, m)
{
    py::class_<ZIPmanager>(m, "ZIPmanager")
        .def(py::init<>())
        .def("compress", &ZIPmanager::compress, "Compress files", py::arg("srcs"), py::arg("output_path"), py::arg("format"), py::arg("password"), py::arg("interval"), py::arg("threads"), py::arg("pg_cb"), py::arg("filename_cb"))
        .def("decompress", &ZIPmanager::decompress, "Decompress files", py::arg("src"), py::arg("output_dir"), py::arg("format"), py::arg("password"), py::arg("interval"), py::arg("threads"), py::arg("pg_cb"), py::arg("filename_cb"));
}